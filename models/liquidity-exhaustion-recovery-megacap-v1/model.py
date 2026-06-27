"""Cross-sectional liquidity exhaustion recovery basket for mega-cap equities.

QFA contract: expose generate_signals(context) -> dict[symbol, weight].
Research-only model; it never places orders.

Mechanism
---------
This model is intentionally divergent from AR-028's single-name extreme
close-location fade. It looks for *breadth* of simultaneous liquidity exhaustion
across a mega-cap basket using only Alpaca/qfa daily OHLCV bars:

- abnormal daily range and volume versus prior-only rolling baselines;
- close-location value (CLV) near the low/high as the side of exhaustion;
- cross-sectional breadth/intensity must be broad enough before any exposure is
  taken;
- once triggered, the allocation is a basket-level recovery trade across the
  liquid mega-cap universe, with only mild tilts toward the names contributing
  most to the exhaustion event.

Daily Alpaca bars do not include auction imbalance, order-book depth, or true
forced-flow labels, so this is a proxy for broad forced selling/buying pressure.
"""

from __future__ import annotations

import math

import pandas as pd

UNIVERSE = ("AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "AVGO", "TSLA", "JPM", "LLY")


class ModelParams:
    volume_z_window = 60
    range_z_window = 60
    min_history = 65
    min_breadth_count = 4
    min_net_intensity = 4.0
    clv_extreme = 0.22  # low <= 0.22; high >= 0.78
    volume_z_min = 0.75
    range_z_min = 0.25
    gross_exposure = 1.0
    basket_floor_fraction = 0.60  # keep mechanism basket-level, not single-name
    max_abs_weight = 0.18


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

    scaled = {s: w / gross for s, w in clean.items()}
    # Iterative cap then renormalize. qfa normalizes again, but keeping the cap
    # here documents the intended construction and avoids concentration in tests.
    capped = dict(scaled)
    for _ in range(5):
        over = {s: max(-max_abs_weight, min(max_abs_weight, w)) for s, w in capped.items()}
        gross_over = sum(abs(w) for w in over.values())
        if gross_over <= 0.0:
            return _zero_weights(symbols)
        capped = {s: w / gross_over for s, w in over.items()}
    return {s: float(PARAMS.gross_exposure * capped.get(s, 0.0)) for s in symbols}


def generate_signals(context):
    """Return basket recovery weights after broad OHLCV exhaustion.

    Downside exhaustion breadth (many names with high-volume, high-range closes
    near lows) produces a long recovery basket. Upside exhaustion breadth
    produces a short recovery basket. The model only trades when the net breadth
    is sufficiently cross-sectional; otherwise it returns all-zero weights.
    """
    output_symbols = list(context.symbols)
    symbols = [s for s in output_symbols if s in UNIVERSE]
    if len(symbols) < PARAMS.min_breadth_count or context.prices.empty:
        return _zero_weights(output_symbols)

    wide = _wide(context.prices, symbols)
    if wide is None:
        return _zero_weights(output_symbols)

    close = wide["close"].dropna(axis=1, how="any")
    tradable = [s for s in symbols if s in close.columns]
    if len(tradable) < PARAMS.min_breadth_count or len(close) < PARAMS.min_history:
        return _zero_weights(output_symbols)

    close = close[tradable]
    high = wide["high"].reindex_like(close)
    low = wide["low"].reindex_like(close)
    volume = wide["volume"].reindex_like(close)

    day_range = (high - low).replace(0.0, pd.NA)
    clv = ((close - low) / day_range).clip(lower=0.0, upper=1.0)
    range_pct = (day_range / close).replace([float("inf"), float("-inf")], pd.NA)

    vol_mean = volume.shift(1).rolling(PARAMS.volume_z_window, min_periods=PARAMS.volume_z_window).mean()
    vol_std = volume.shift(1).rolling(PARAMS.volume_z_window, min_periods=PARAMS.volume_z_window).std()
    rng_mean = range_pct.shift(1).rolling(PARAMS.range_z_window, min_periods=PARAMS.range_z_window).mean()
    rng_std = range_pct.shift(1).rolling(PARAMS.range_z_window, min_periods=PARAMS.range_z_window).std()

    vol_z = ((volume - vol_mean) / vol_std.replace(0.0, pd.NA)).replace([float("inf"), float("-inf")], pd.NA)
    rng_z = ((range_pct - rng_mean) / rng_std.replace(0.0, pd.NA)).replace([float("inf"), float("-inf")], pd.NA)

    latest = close.index[-1]
    sell_scores: dict[str, float] = {}
    buy_scores: dict[str, float] = {}
    for symbol in tradable:
        loc = clv.loc[latest, symbol]
        vz = vol_z.loc[latest, symbol]
        rz = rng_z.loc[latest, symbol]
        if pd.isna(loc) or pd.isna(vz) or pd.isna(rz):
            continue
        vz = float(vz)
        rz = float(rz)
        loc = float(loc)
        if vz < PARAMS.volume_z_min or rz < PARAMS.range_z_min:
            continue
        intensity = (1.0 + max(0.0, vz - PARAMS.volume_z_min)) * (1.0 + max(0.0, rz - PARAMS.range_z_min))
        if loc <= PARAMS.clv_extreme:
            sell_scores[symbol] = intensity * (PARAMS.clv_extreme - loc + 0.01)
        elif loc >= 1.0 - PARAMS.clv_extreme:
            buy_scores[symbol] = intensity * (loc - (1.0 - PARAMS.clv_extreme) + 0.01)

    sell_count = len(sell_scores)
    buy_count = len(buy_scores)
    sell_intensity = sum(sell_scores.values())
    buy_intensity = sum(buy_scores.values())
    net_count = sell_count - buy_count
    net_intensity = sell_intensity - buy_intensity

    if abs(net_count) < PARAMS.min_breadth_count or abs(net_intensity) < PARAMS.min_net_intensity:
        return _zero_weights(output_symbols)

    # Broad forced selling -> next-period long recovery basket; broad forced
    # buying -> next-period short recovery basket.
    direction = 1.0 if net_intensity > 0.0 else -1.0
    active_scores = sell_scores if direction > 0.0 else buy_scores
    active_total = sum(active_scores.values())

    # Basket-level construction: every tradable universe member receives a base
    # allocation in the recovery direction, with a minority tilt toward names
    # participating in the exhaustion event.
    equal_component = PARAMS.basket_floor_fraction / len(tradable)
    tilt_fraction = 1.0 - PARAMS.basket_floor_fraction
    raw = {s: 0.0 for s in output_symbols}
    for symbol in tradable:
        tilt = 0.0
        if active_total > 0.0:
            tilt = tilt_fraction * active_scores.get(symbol, 0.0) / active_total
        raw[symbol] = direction * (equal_component + tilt)

    return _normalize_with_cap(raw, output_symbols, PARAMS.max_abs_weight)
