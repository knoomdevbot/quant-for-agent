"""Sector ETF earnings-season dispersion reversal alpha.

QFA contract: expose generate_signals(context) -> dict[symbol, weight].
Research-only model; it never places orders.

Hypothesis: when sector ETF residual returns disperse unusually during earnings
season, sector-level hedges and flows can overshoot and partially mean-revert over
subsequent sessions. The model uses only daily ETF OHLCV available through qfa /
Alpaca: no earnings calendar, fundamentals, options data, or local CSV input.
"""

from __future__ import annotations

import math

import pandas as pd

SECTOR_ETFS = ("XLK", "XLY", "XLP", "XLV", "XLF", "XLI", "XLE", "XLU", "XLB", "XLRE")
UNIVERSE = SECTOR_ETFS + ("SPY",)


class ModelParams:
    residual_lookback = 5
    dispersion_window = 60
    min_history = 90
    min_sector_count = 8
    dispersion_z_entry = 0.75
    residual_z_entry = 0.40
    max_abs_weight = 0.18
    spy_hedge_fraction = 0.0  # sector-dollar-neutral already removes broad beta proxy.


PARAMS = ModelParams()


def _zero_weights(symbols):
    return {symbol: 0.0 for symbol in symbols}


def _is_earnings_season(ts: pd.Timestamp) -> bool:
    """Approximate US earnings-season weeks without external calendar data."""
    month = int(ts.month)
    day = int(ts.day)
    # Most index constituents report from mid-Jan/Apr/Jul/Oct through the first
    # half of the following month. This is an ex-ante calendar proxy.
    return (month in {1, 4, 7, 10} and day >= 10) or (month in {2, 5, 8, 11} and day <= 15)


def _cap_and_normalize(weights: dict[str, float], max_abs_weight: float) -> dict[str, float]:
    clean = {s: float(w) for s, w in weights.items() if math.isfinite(float(w))}
    gross = sum(abs(w) for w in clean.values())
    if gross <= 0.0:
        return {s: 0.0 for s in weights}
    scaled = {s: w / gross for s, w in clean.items()}
    capped = {s: max(-max_abs_weight, min(max_abs_weight, w)) for s, w in scaled.items()}
    capped_gross = sum(abs(w) for w in capped.values())
    if capped_gross <= 0.0:
        return {s: 0.0 for s in weights}
    return {s: float(capped.get(s, 0.0) / capped_gross) for s in weights}


def generate_signals(context):
    """Return target weights for sector residual mean reversion.

    Signal steps:
    1. Build close-to-close returns for selected sector ETFs and SPY.
    2. Compute 5-day sector residual returns versus SPY.
    3. Measure latest cross-sector residual dispersion versus its prior 60-day
       distribution. Trade only during approximate earnings-season windows.
    4. Fade sectors with extreme 5-day residual z-scores: overweight recent
       residual losers and underweight recent residual winners.
    5. Dollar-neutralize across sectors, cap concentration, and gross normalize.
    """
    output_symbols = list(context.symbols)
    symbols = [s for s in output_symbols if s in UNIVERSE]
    if "SPY" not in symbols or len([s for s in symbols if s in SECTOR_ETFS]) < PARAMS.min_sector_count:
        return _zero_weights(output_symbols)
    if context.prices.empty:
        return _zero_weights(output_symbols)

    px = context.prices[context.prices["symbol"].isin(symbols)].copy()
    if px.empty:
        return _zero_weights(output_symbols)
    px["timestamp"] = pd.to_datetime(px["timestamp"], utc=True)
    close = px.pivot(index="timestamp", columns="symbol", values="close").sort_index().ffill()
    tradable_sectors = [s for s in SECTOR_ETFS if s in close.columns]
    cols = tradable_sectors + ["SPY"]
    close = close[cols].dropna()
    if len(close) < PARAMS.min_history or len(tradable_sectors) < PARAMS.min_sector_count:
        return _zero_weights(output_symbols)

    latest = close.index[-1]
    if not _is_earnings_season(latest):
        return _zero_weights(output_symbols)

    returns = close.pct_change()
    sector_ret = returns[tradable_sectors]
    spy_ret = returns["SPY"]
    residual = sector_ret.sub(spy_ret, axis=0)
    residual_sum = residual.rolling(PARAMS.residual_lookback, min_periods=PARAMS.residual_lookback).sum()
    dispersion = residual_sum.std(axis=1)
    disp_mean = dispersion.shift(1).rolling(PARAMS.dispersion_window, min_periods=PARAMS.dispersion_window).mean()
    disp_std = dispersion.shift(1).rolling(PARAMS.dispersion_window, min_periods=PARAMS.dispersion_window).std()
    if pd.isna(dispersion.iloc[-1]) or pd.isna(disp_mean.iloc[-1]) or pd.isna(disp_std.iloc[-1]) or float(disp_std.iloc[-1]) <= 0:
        return _zero_weights(output_symbols)
    dispersion_z = float((dispersion.iloc[-1] - disp_mean.iloc[-1]) / disp_std.iloc[-1])
    if dispersion_z < PARAMS.dispersion_z_entry:
        return _zero_weights(output_symbols)

    latest_resid = residual_sum.iloc[-1]
    resid_mean = residual_sum.shift(1).rolling(PARAMS.dispersion_window, min_periods=PARAMS.dispersion_window).mean().iloc[-1]
    resid_std = residual_sum.shift(1).rolling(PARAMS.dispersion_window, min_periods=PARAMS.dispersion_window).std().iloc[-1]
    resid_z = ((latest_resid - resid_mean) / resid_std).replace([float("inf"), float("-inf")], pd.NA).dropna()
    resid_z = resid_z[[s for s in tradable_sectors if s in resid_z.index]]
    resid_z = resid_z[resid_z.abs() >= PARAMS.residual_z_entry]
    if len(resid_z) < 2:
        return _zero_weights(output_symbols)

    # Contrarian score: large positive residual -> short; large negative -> long.
    raw_scores = -resid_z.astype(float)
    raw_scores = raw_scores - raw_scores.mean()  # sector-dollar-neutralize.
    if raw_scores.abs().sum() <= 0:
        return _zero_weights(output_symbols)

    raw = {s: 0.0 for s in output_symbols}
    for symbol, score in raw_scores.items():
        raw[symbol] = float(score)
    if PARAMS.spy_hedge_fraction:
        raw["SPY"] = -PARAMS.spy_hedge_fraction * sum(raw.get(s, 0.0) for s in tradable_sectors)
    return _cap_and_normalize(raw, PARAMS.max_abs_weight)
