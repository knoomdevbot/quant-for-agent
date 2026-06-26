"""Mega-cap range-compression breakout continuation model (AR-057).

QFA contract: expose generate_signals(context) -> dict[symbol, weight].
Research only; never places orders.

Mechanism
---------
The model looks for liquid mega-cap names whose realized range has compressed
versus its own prior distribution, then breaks above/below a prior multi-week
channel on expanding volume. Signals are continuation-oriented (long upside
breakouts, short downside breakouts), volatility-scaled, and lightly gated by a
basket market trend so the strategy is not simply buying every noisy high.
"""

from __future__ import annotations

import math

import pandas as pd

UNIVERSE = ("AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "AVGO", "TSLA", "JPM", "LLY")


class ModelParams:
    compression_lookback = 15
    compression_rank_window = 90
    compression_quantile_max = 0.35
    breakout_lookback = 40
    recent_breakout_days = 3
    volume_z_window = 60
    volume_z_min = 0.75
    vol_window = 20
    market_trend_window = 50
    min_history = 120
    gross_exposure = 1.0
    max_abs_weight = 0.20
    min_active_names = 1


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
    for _ in range(8):
        capped = {s: max(-max_abs_weight, min(max_abs_weight, w)) for s, w in capped.items()}
        gross = sum(abs(w) for w in capped.values())
        if gross <= 0.0:
            return _zero_weights(symbols)
        capped = {s: w / gross for s, w in capped.items()}
    return {s: float(PARAMS.gross_exposure * capped.get(s, 0.0)) for s in symbols}


def _range_compression_quantile(range_pct: pd.DataFrame) -> pd.DataFrame:
    smooth_range = range_pct.rolling(
        PARAMS.compression_lookback, min_periods=PARAMS.compression_lookback
    ).mean()

    def pct_rank_last(x):
        last = x[-1]
        if pd.isna(last):
            return float("nan")
        return float((x <= last).mean())

    return smooth_range.shift(1).rolling(
        PARAMS.compression_rank_window, min_periods=PARAMS.compression_rank_window
    ).apply(pct_rank_last, raw=True)


def generate_signals(context):
    """Return weights for recent compression breakouts.

    Uses prior-only channels and baselines. A name qualifies when, within the
    last three sessions, it closed beyond a prior 40-day high/low after a low
    range-quantile setup and with positive volume z-score. Scores decay with
    event age and scale inversely to realized volatility.
    """
    output_symbols = list(context.symbols)
    symbols = [s for s in output_symbols if s in UNIVERSE]
    if not symbols or context.prices.empty:
        return _zero_weights(output_symbols)

    wide = _wide(context.prices, symbols)
    if wide is None:
        return _zero_weights(output_symbols)

    close = wide["close"].dropna(axis=1, how="any")
    tradable = [s for s in symbols if s in close.columns]
    if not tradable or len(close) < PARAMS.min_history:
        return _zero_weights(output_symbols)

    close = close[tradable]
    high = wide["high"].reindex_like(close)
    low = wide["low"].reindex_like(close)
    volume = wide["volume"].reindex_like(close)
    returns = close.pct_change()

    range_pct = ((high - low) / close).replace([float("inf"), float("-inf")], pd.NA)
    compression_q = _range_compression_quantile(range_pct)
    prior_high = high.shift(1).rolling(PARAMS.breakout_lookback, min_periods=PARAMS.breakout_lookback).max()
    prior_low = low.shift(1).rolling(PARAMS.breakout_lookback, min_periods=PARAMS.breakout_lookback).min()
    vol_mean = volume.shift(1).rolling(PARAMS.volume_z_window, min_periods=PARAMS.volume_z_window).mean()
    vol_std = volume.shift(1).rolling(PARAMS.volume_z_window, min_periods=PARAMS.volume_z_window).std()
    volume_z = ((volume - vol_mean) / vol_std.replace(0.0, pd.NA)).replace(
        [float("inf"), float("-inf")], pd.NA
    )
    realized_vol = returns.shift(1).rolling(PARAMS.vol_window, min_periods=PARAMS.vol_window).std()

    market = close.mean(axis=1)
    market_trend = market / market.shift(PARAMS.market_trend_window) - 1.0
    trend_latest = float(market_trend.iloc[-1]) if not pd.isna(market_trend.iloc[-1]) else 0.0

    raw = {s: 0.0 for s in output_symbols}
    latest_pos = len(close) - 1
    for symbol in tradable:
        best_score = 0.0
        best_direction = 0.0
        for age in range(PARAMS.recent_breakout_days):
            pos = latest_pos - age
            if pos < 0:
                continue
            date = close.index[pos]
            cq = compression_q.loc[date, symbol]
            vz = volume_z.loc[date, symbol]
            if pd.isna(cq) or pd.isna(vz) or cq > PARAMS.compression_quantile_max or vz < PARAMS.volume_z_min:
                continue
            c = close.loc[date, symbol]
            ph = prior_high.loc[date, symbol]
            pl = prior_low.loc[date, symbol]
            if pd.isna(c) or pd.isna(ph) or pd.isna(pl):
                continue
            direction = 0.0
            breakout_strength = 0.0
            if c > ph and trend_latest >= -0.03:
                direction = 1.0
                breakout_strength = float(c / ph - 1.0)
            elif c < pl and trend_latest <= 0.05:
                direction = -1.0
                breakout_strength = float(pl / c - 1.0)
            if direction == 0.0 or breakout_strength <= 0.0:
                continue
            rv = realized_vol.loc[date, symbol]
            if pd.isna(rv) or float(rv) <= 0.0:
                continue
            decay = (PARAMS.recent_breakout_days - age) / PARAMS.recent_breakout_days
            compression_bonus = 1.0 + (PARAMS.compression_quantile_max - float(cq))
            volume_bonus = 1.0 + min(2.0, float(vz) - PARAMS.volume_z_min)
            score = decay * compression_bonus * volume_bonus * breakout_strength / max(float(rv), 0.005)
            if score > best_score:
                best_score = score
                best_direction = direction
        if best_direction != 0.0:
            raw[symbol] = best_direction * best_score

    if sum(1 for w in raw.values() if abs(w) > 0.0) < PARAMS.min_active_names:
        return _zero_weights(output_symbols)
    return _normalize_with_cap(raw, output_symbols, PARAMS.max_abs_weight)
