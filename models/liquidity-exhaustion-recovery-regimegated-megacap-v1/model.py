"""Regime-gated liquidity exhaustion recovery basket for mega-cap equities.

QFA contract: expose generate_signals(context) -> dict[symbol, weight].
Research-only model; it never places orders.

This refines AR-046 by retaining its cross-sectional abnormal range/volume
close-location exhaustion breadth trigger, but only trades when the broad basket
looks more likely to mean-revert than trend: the equal-weight mega-cap proxy is
above its medium trend, realized volatility is elevated but not in the highest
crisis tail, and the most recent exhaustion event is not inside a short cooldown.
Signals persist with deterministic decay for a few sessions after a qualifying
event, keeping turnover sparse without any mutable state.
"""

from __future__ import annotations

import math

import pandas as pd

UNIVERSE = ("AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "AVGO", "TSLA", "JPM", "LLY")


class ModelParams:
    volume_z_window = 60
    range_z_window = 60
    vol_window = 20
    vol_percentile_window = 126
    trend_lookback = 80
    min_history = 190
    breadth_threshold = 0.40  # 4/10 symbols; within requested 30-60% range
    min_net_intensity = 4.5
    clv_extreme = 0.24
    volume_z_min = 1.10
    range_z_min = 0.75
    max_vol_percentile = 0.82
    min_vol_percentile = 0.35
    max_trend_drawdown = -0.10
    signal_decay_days = 3
    cooldown_days = 3
    gross_exposure = 0.80
    basket_floor_fraction = 0.70
    max_abs_weight = 0.16


PARAMS = ModelParams()


def _zero_weights(symbols):
    return {symbol: 0.0 for symbol in symbols}


def _wide(prices: pd.DataFrame, symbols: list[str]):
    px = prices[prices["symbol"].isin(symbols)].copy()
    if px.empty:
        return None
    px["timestamp"] = pd.to_datetime(px["timestamp"], utc=True)
    px = px.sort_values(["timestamp", "symbol"])
    out = {}
    for col in ("high", "low", "close", "volume"):
        out[col] = px.pivot(index="timestamp", columns="symbol", values=col).sort_index().ffill()
    return out


def _normalize_with_cap(weights: dict[str, float], symbols: list[str], max_abs_weight: float) -> dict[str, float]:
    clean = {s: float(weights.get(s, 0.0)) for s in symbols}
    clean = {s: (w if math.isfinite(w) else 0.0) for s, w in clean.items()}
    gross = sum(abs(w) for w in clean.values())
    if gross <= 0.0:
        return _zero_weights(symbols)
    capped = {s: w / gross for s, w in clean.items()}
    for _ in range(6):
        capped = {s: max(-max_abs_weight, min(max_abs_weight, w)) for s, w in capped.items()}
        gross_capped = sum(abs(w) for w in capped.values())
        if gross_capped <= 0.0:
            return _zero_weights(symbols)
        capped = {s: w / gross_capped for s, w in capped.items()}
    return {s: float(PARAMS.gross_exposure * capped.get(s, 0.0)) for s in symbols}


def _event_state(close, high, low, volume, tradable):
    day_range = (high - low).replace(0.0, pd.NA)
    clv = ((close - low) / day_range).clip(lower=0.0, upper=1.0)
    range_pct = (day_range / close).replace([float("inf"), float("-inf")], pd.NA)

    vol_mean = volume.shift(1).rolling(PARAMS.volume_z_window, min_periods=PARAMS.volume_z_window).mean()
    vol_std = volume.shift(1).rolling(PARAMS.volume_z_window, min_periods=PARAMS.volume_z_window).std()
    rng_mean = range_pct.shift(1).rolling(PARAMS.range_z_window, min_periods=PARAMS.range_z_window).mean()
    rng_std = range_pct.shift(1).rolling(PARAMS.range_z_window, min_periods=PARAMS.range_z_window).std()
    vol_z = ((volume - vol_mean) / vol_std.replace(0.0, pd.NA)).replace([float("inf"), float("-inf")], pd.NA)
    rng_z = ((range_pct - rng_mean) / rng_std.replace(0.0, pd.NA)).replace([float("inf"), float("-inf")], pd.NA)

    events = []
    min_count = max(3, int(math.ceil(PARAMS.breadth_threshold * len(tradable))))
    for ts in close.index:
        sell_scores: dict[str, float] = {}
        buy_scores: dict[str, float] = {}
        for symbol in tradable:
            loc = clv.at[ts, symbol]
            vz = vol_z.at[ts, symbol]
            rz = rng_z.at[ts, symbol]
            if pd.isna(loc) or pd.isna(vz) or pd.isna(rz):
                continue
            loc = float(loc)
            vz = float(vz)
            rz = float(rz)
            if vz < PARAMS.volume_z_min or rz < PARAMS.range_z_min:
                continue
            intensity = (1.0 + max(0.0, vz - PARAMS.volume_z_min)) * (1.0 + max(0.0, rz - PARAMS.range_z_min))
            if loc <= PARAMS.clv_extreme:
                sell_scores[symbol] = intensity * (PARAMS.clv_extreme - loc + 0.01)
            elif loc >= 1.0 - PARAMS.clv_extreme:
                buy_scores[symbol] = intensity * (loc - (1.0 - PARAMS.clv_extreme) + 0.01)
        net_count = len(sell_scores) - len(buy_scores)
        net_intensity = sum(sell_scores.values()) - sum(buy_scores.values())
        if abs(net_count) >= min_count and abs(net_intensity) >= PARAMS.min_net_intensity:
            direction = 1.0 if net_intensity > 0.0 else -1.0
            active_scores = sell_scores if direction > 0 else buy_scores
            events.append((ts, direction, active_scores, abs(net_intensity)))
    return events


def _regime_ok(close: pd.DataFrame) -> bool:
    ew = close.mean(axis=1).dropna()
    if len(ew) < PARAMS.min_history:
        return False
    ret = ew.pct_change().dropna()
    realized_vol = ret.rolling(PARAMS.vol_window, min_periods=PARAMS.vol_window).std() * math.sqrt(252.0)
    vol_hist = realized_vol.dropna()
    if len(vol_hist) < PARAMS.vol_percentile_window:
        return False
    latest_vol = float(vol_hist.iloc[-1])
    pct = float((vol_hist.iloc[-PARAMS.vol_percentile_window:] <= latest_vol).mean())
    trend_ma = ew.shift(1).rolling(PARAMS.trend_lookback, min_periods=PARAMS.trend_lookback).mean().iloc[-1]
    if pd.isna(trend_ma) or trend_ma <= 0:
        return False
    trend_gap = float(ew.iloc[-1] / trend_ma - 1.0)
    return (PARAMS.min_vol_percentile <= pct <= PARAMS.max_vol_percentile) and (trend_gap >= PARAMS.max_trend_drawdown)


def generate_signals(context):
    """Return regime-gated basket recovery weights.

    Broad downside exhaustion produces a long basket; broad upside exhaustion
    produces a short basket, but only after a qualifying historical event within
    the decay window and not immediately after another event cooldown conflict.
    """
    output_symbols = list(context.symbols)
    symbols = [s for s in output_symbols if s in UNIVERSE]
    if len(symbols) < 4 or context.prices.empty:
        return _zero_weights(output_symbols)

    wide = _wide(context.prices, symbols)
    if wide is None:
        return _zero_weights(output_symbols)
    close = wide["close"].dropna(axis=1, how="any")
    tradable = [s for s in symbols if s in close.columns]
    if len(tradable) < 4 or len(close) < PARAMS.min_history:
        return _zero_weights(output_symbols)
    close = close[tradable]
    high = wide["high"].reindex_like(close)
    low = wide["low"].reindex_like(close)
    volume = wide["volume"].reindex_like(close)

    if not _regime_ok(close):
        return _zero_weights(output_symbols)

    events = _event_state(close, high, low, volume, tradable)
    if not events:
        return _zero_weights(output_symbols)
    dates = list(close.index)
    latest_idx = len(dates) - 1
    recent = []
    for event in events:
        event_idx = dates.index(event[0])
        age = latest_idx - event_idx
        if 0 <= age <= PARAMS.signal_decay_days:
            recent.append((age, event))
    if not recent:
        return _zero_weights(output_symbols)
    age, (_, direction, active_scores, _) = sorted(recent, key=lambda x: x[0])[0]

    # Cooldown: if a newer opposite-direction exhaustion occurred, stand aside.
    for event_ts, event_dir, _, _ in events:
        event_idx = dates.index(event_ts)
        if 0 <= latest_idx - event_idx <= PARAMS.cooldown_days and event_dir != direction and event_idx > latest_idx - age:
            return _zero_weights(output_symbols)

    active_total = sum(active_scores.values())
    decay = max(0.0, (PARAMS.signal_decay_days + 1 - age) / (PARAMS.signal_decay_days + 1))
    equal_component = PARAMS.basket_floor_fraction / len(tradable)
    tilt_fraction = 1.0 - PARAMS.basket_floor_fraction
    raw = {s: 0.0 for s in output_symbols}
    for symbol in tradable:
        tilt = tilt_fraction * active_scores.get(symbol, 0.0) / active_total if active_total > 0 else 0.0
        raw[symbol] = direction * decay * (equal_component + tilt)
    return _normalize_with_cap(raw, output_symbols, PARAMS.max_abs_weight)
