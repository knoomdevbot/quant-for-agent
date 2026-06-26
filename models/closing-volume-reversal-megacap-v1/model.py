"""Abnormal close-location/volume reversal alpha for mega-cap equities.

QFA contract: expose generate_signals(context) -> dict[symbol, weight].
Research-only model; it never places orders.

Important data limitation
-------------------------
Alpaca/qfa daily bars do not expose closing-auction imbalance or auction-only
volume. This model therefore uses a documented proxy for "closing-auction-like"
pressure: the latest completed daily bar's close location within its high-low
range, gated by abnormal share and dollar volume. It is not a direct inversion
of AR-009's multi-day volume-confirmed price-pressure continuation; it targets
one-bar liquidity provision after an abnormal end-of-day close near the high/low.
"""

from __future__ import annotations

import math

import pandas as pd

UNIVERSE = ("AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA")


class ModelParams:
    volume_z_window = 60
    volume_z_min = 1.25
    dollar_volume_z_min = 1.25
    close_location_extreme = 0.8
    range_z_window = 60
    range_z_min = -0.25
    max_abs_weight = 0.25
    min_symbols = 3


PARAMS = ModelParams()


def _zero_weights(symbols):
    return {symbol: 0.0 for symbol in symbols}


def _cap_and_normalize(weights: dict[str, float], max_abs_weight: float) -> dict[str, float]:
    clean = {s: float(w) for s, w in weights.items() if math.isfinite(float(w))}
    gross = sum(abs(w) for w in clean.values())
    if not clean or gross <= 0.0:
        return {s: 0.0 for s in weights}

    scaled = {s: w / gross for s, w in clean.items()}
    capped = {s: max(-max_abs_weight, min(max_abs_weight, w)) for s, w in scaled.items()}
    capped_gross = sum(abs(w) for w in capped.values())
    if capped_gross <= 0.0:
        return {s: 0.0 for s in weights}
    return {s: float(capped.get(s, 0.0) / capped_gross) for s in weights}


def _wide_ohlcv(prices: pd.DataFrame, symbols: list[str]):
    px = prices[prices["symbol"].isin(symbols)].copy()
    if px.empty:
        return None
    px["timestamp"] = pd.to_datetime(px["timestamp"], utc=True)
    px = px.sort_values(["timestamp", "symbol"])
    wide = {}
    for col in ("high", "low", "close", "volume"):
        wide[col] = px.pivot(index="timestamp", columns="symbol", values=col).sort_index().ffill()
    return wide


def generate_signals(context):
    """Return contrarian weights after abnormal volume at an extreme close.

    Signal definition:
    - Close location value (CLV) = (close - low) / (high - low).
    - Treat CLV >= 0.80 as an extreme high close and CLV <= 0.20 as an extreme
      low close, a daily-bar proxy for end-of-day/closing-pressure imbalance.
    - Require abnormal share volume or abnormal dollar volume versus a prior-only
      60-session z-score baseline; require the day's range not to be unusually
      compressed, to reduce noise from tiny ranges.
    - Fade the pressure for the next qfa close-to-close period: high close on
      abnormal volume -> short; low close on abnormal volume -> long.
    - Gross-normalize to 1.0 and cap single-name absolute concentration.
    """
    output_symbols = list(context.symbols)
    symbols = [s for s in output_symbols if s in UNIVERSE]
    required_rows = max(PARAMS.volume_z_window, PARAMS.range_z_window) + 2
    if len(symbols) < PARAMS.min_symbols or context.prices.empty:
        return _zero_weights(output_symbols)

    wide = _wide_ohlcv(context.prices, symbols)
    if wide is None:
        return _zero_weights(output_symbols)

    close = wide["close"].dropna(axis=1, how="any")
    high = wide["high"].reindex_like(close)
    low = wide["low"].reindex_like(close)
    volume = wide["volume"].reindex_like(close)
    tradable = [s for s in symbols if s in close.columns]
    if len(tradable) < PARAMS.min_symbols or len(close) < required_rows:
        return _zero_weights(output_symbols)

    close = close[tradable]
    high = high[tradable]
    low = low[tradable]
    volume = volume[tradable]
    day_range = (high - low).replace(0.0, pd.NA)
    dollar_volume = close * volume
    clv = ((close - low) / day_range).clip(lower=0.0, upper=1.0)
    range_pct = (day_range / close).replace([float("inf"), float("-inf")], pd.NA)

    vol_mean = volume.shift(1).rolling(PARAMS.volume_z_window, min_periods=PARAMS.volume_z_window).mean()
    vol_std = volume.shift(1).rolling(PARAMS.volume_z_window, min_periods=PARAMS.volume_z_window).std()
    dvol_mean = dollar_volume.shift(1).rolling(PARAMS.volume_z_window, min_periods=PARAMS.volume_z_window).mean()
    dvol_std = dollar_volume.shift(1).rolling(PARAMS.volume_z_window, min_periods=PARAMS.volume_z_window).std()
    range_mean = range_pct.shift(1).rolling(PARAMS.range_z_window, min_periods=PARAMS.range_z_window).mean()
    range_std = range_pct.shift(1).rolling(PARAMS.range_z_window, min_periods=PARAMS.range_z_window).std()

    vol_z = ((volume - vol_mean) / vol_std.replace(0.0, pd.NA)).replace([float("inf"), float("-inf")], pd.NA)
    dvol_z = ((dollar_volume - dvol_mean) / dvol_std.replace(0.0, pd.NA)).replace([float("inf"), float("-inf")], pd.NA)
    range_z = ((range_pct - range_mean) / range_std.replace(0.0, pd.NA)).replace([float("inf"), float("-inf")], pd.NA)

    latest = close.index[-1]
    raw = {s: 0.0 for s in output_symbols}
    for symbol in tradable:
        loc = clv.loc[latest, symbol]
        vz = vol_z.loc[latest, symbol]
        dvz = dvol_z.loc[latest, symbol]
        rz = range_z.loc[latest, symbol]
        if pd.isna(loc) or pd.isna(vz) or pd.isna(dvz) or pd.isna(rz):
            continue
        if float(rz) < PARAMS.range_z_min:
            continue

        loc = float(loc)
        upper_excess = max(0.0, loc - PARAMS.close_location_extreme)
        lower_excess = max(0.0, (1.0 - PARAMS.close_location_extreme) - loc)
        if upper_excess <= 0.0 and lower_excess <= 0.0:
            continue

        share_abn = max(0.0, float(vz) - PARAMS.volume_z_min)
        dollar_abn = max(0.0, float(dvz) - PARAMS.dollar_volume_z_min)
        volume_confirmation = max(share_abn, dollar_abn)
        if volume_confirmation <= 0.0:
            continue

        # Contrarian liquidity-provision score, not a multi-day return inversion.
        pressure_side = upper_excess - lower_excess  # positive means close near high
        raw[symbol] = -pressure_side * (1.0 + volume_confirmation)

    return _cap_and_normalize(raw, PARAMS.max_abs_weight)
