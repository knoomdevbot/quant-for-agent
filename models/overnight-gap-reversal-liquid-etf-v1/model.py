"""Open-aware overnight gap reversal alpha for liquid ETFs.

QFA contract: expose generate_signals(context) -> dict[symbol, weight].
Research-only model; it never places orders.

Intended economics: observe today's open relative to yesterday's close and fade
large normalized overnight gaps for an intraday open-to-close hold. The qfa daily
close-to-close backtester cannot enter at the current open, so this function is
a qfa-compatible *lagged proxy* using the latest completed bar's gap and applying
weights to the next qfa period. The accompanying evaluation artifacts use direct
Alpaca-backed OHLC bars to measure the intended same-day open-to-close horizon.
"""

from __future__ import annotations

import math

import pandas as pd

UNIVERSE = ("SPY", "QQQ", "IWM", "TLT", "GLD", "SLV", "XLF", "XLK", "XLE", "XLV")


class ModelParams:
    gap_z_window = 60
    entry_z = 1.5
    market_filter = True
    max_abs_weight = 0.25
    min_symbols = 5


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
    return {
        col: px.pivot(index="timestamp", columns="symbol", values=col).sort_index().ffill()
        for col in ("open", "close")
    }


def generate_signals(context):
    """Return contrarian ETF target weights after large normalized overnight gaps.

    Signal definition:
    - Daily overnight gap = open_t / close_{t-1} - 1.
    - Prior-only rolling z-score over PARAMS.gap_z_window bars.
    - If latest completed bar's z-score exceeds +/- entry_z, fade it:
      large positive gap -> short, large negative gap -> long.
    - Score is excess absolute z-score above threshold.
    - Gross-normalize to 1.0 and cap absolute single-ETF concentration.

    Feasibility limitation: qfa's current daily backtester calls this after the
    bar is complete and applies weights to the next close-to-close period. Use
    the research evaluation artifacts for the intended same-day open-to-close
    measurement on Alpaca OHLC bars.
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
    rolling_mean = gap.shift(1).rolling(PARAMS.gap_z_window, min_periods=PARAMS.gap_z_window).mean()
    rolling_std = gap.shift(1).rolling(PARAMS.gap_z_window, min_periods=PARAMS.gap_z_window).std()
    gap_z = ((gap - rolling_mean) / rolling_std).replace([float("inf"), float("-inf")], pd.NA)

    latest = gap_z.index[-1]
    raw = {s: 0.0 for s in output_symbols}

    # Optional broad-gap filter: when SPY itself has a large normalized gap,
    # skip the day rather than fading a likely macro/news gap across ETFs.
    if PARAMS.market_filter and "SPY" in tradable:
        spy_z = gap_z.loc[latest, "SPY"]
        if pd.notna(spy_z) and abs(float(spy_z)) >= PARAMS.entry_z:
            return _zero_weights(output_symbols)

    for symbol in tradable:
        z = gap_z.loc[latest, symbol]
        if pd.isna(z):
            continue
        z = float(z)
        if abs(z) < PARAMS.entry_z:
            continue
        raw[symbol] = -math.copysign(abs(z) - PARAMS.entry_z, z)

    return _cap_and_normalize(raw, PARAMS.max_abs_weight)
