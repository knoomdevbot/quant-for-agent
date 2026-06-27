"""Overnight gap reversal alpha for liquid mega-cap equities.

QFA contract: expose generate_signals(context) -> dict[symbol, weight].
Research-only model; it never places orders.

Daily qfa backtests evaluate weights from the latest completed bar on the
following close-to-close return. That means this implementation cannot truly
enter at the same-day open after observing an overnight gap. It uses the latest
completed bar's open-vs-prior-close gap as a lagged proxy and holds the
contrarian position for the next qfa period.
"""

from __future__ import annotations

import math

import pandas as pd

UNIVERSE = ("AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA")


class ModelParams:
    gap_z_window = 60
    entry_z = 1.0
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


def _wide_ohlc(prices: pd.DataFrame, symbols: list[str]):
    px = prices[prices["symbol"].isin(symbols)].copy()
    if px.empty:
        return None
    px["timestamp"] = pd.to_datetime(px["timestamp"], utc=True)
    wide = {}
    for col in ("open", "close"):
        wide[col] = px.pivot(index="timestamp", columns="symbol", values=col).sort_index().ffill()
    return wide


def generate_signals(context):
    """Return contrarian target weights after large overnight gaps.

    Signal definition:
    - For each symbol, compute daily overnight gap = open / prior close - 1.
    - Estimate a prior-only rolling z-score over PARAMS.gap_z_window bars.
    - If latest completed bar's gap z-score exceeds +/- entry_z, fade it:
      large positive gap -> short, large negative gap -> long.
    - Score magnitude is excess absolute z-score above threshold.
    - Gross-normalize to 1.0 and cap single-name absolute concentration.

    Feasibility limitation:
    qfa daily bars provide OHLCV but the backtest calls generate_signals after
    the latest completed bar and applies weights to the next close-to-close
    return. Therefore this is a lagged next-period proxy for an intended
    open-to-close overnight-gap reversal strategy, not a true same-day-at-open
    execution simulation.
    """
    output_symbols = list(context.symbols)
    symbols = [s for s in output_symbols if s in UNIVERSE]
    if len(symbols) < PARAMS.min_symbols or context.prices.empty:
        return _zero_weights(output_symbols)

    wide = _wide_ohlc(context.prices, symbols)
    if wide is None:
        return _zero_weights(output_symbols)

    open_ = wide["open"].dropna(axis=1, how="any")
    close = wide["close"].reindex_like(open_)
    tradable = [s for s in symbols if s in open_.columns]
    if len(tradable) < PARAMS.min_symbols or len(open_) < PARAMS.gap_z_window + 2:
        return _zero_weights(output_symbols)

    open_ = open_[tradable]
    close = close[tradable]
    gap = (open_ / close.shift(1) - 1.0).replace([float("inf"), float("-inf")], pd.NA)

    # Prior-only z-score avoids using the latest gap in its own mean/std estimate.
    rolling_mean = gap.shift(1).rolling(PARAMS.gap_z_window, min_periods=PARAMS.gap_z_window).mean()
    rolling_std = gap.shift(1).rolling(PARAMS.gap_z_window, min_periods=PARAMS.gap_z_window).std()
    gap_z = ((gap - rolling_mean) / rolling_std).replace([float("inf"), float("-inf")], pd.NA)

    latest = gap_z.index[-1]
    raw = {s: 0.0 for s in output_symbols}
    for symbol in tradable:
        z = gap_z.loc[latest, symbol]
        if pd.isna(z):
            continue
        z = float(z)
        if abs(z) < PARAMS.entry_z:
            continue
        # Contrarian: fade large positive gaps; buy large negative gaps.
        raw[symbol] = -math.copysign(abs(z) - PARAMS.entry_z, z)

    return _cap_and_normalize(raw, PARAMS.max_abs_weight)
