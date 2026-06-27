"""Volatility breakout continuation alpha for liquid mega-cap equities.

QFA contract: expose generate_signals(context) -> dict[symbol, weight].
Research-only model; it never places orders.
"""

from __future__ import annotations

import math

import pandas as pd


UNIVERSE = ("AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA")


class ModelParams:
    atr_window = 20
    breakout_threshold = 1.5
    close_location_filter = 0.8
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


def _ohlc(prices: pd.DataFrame, symbols: list[str]):
    px = prices[prices["symbol"].isin(symbols)].copy()
    if px.empty:
        return None
    px["timestamp"] = pd.to_datetime(px["timestamp"], utc=True)
    wide = {}
    for col in ("open", "high", "low", "close"):
        wide[col] = px.pivot(index="timestamp", columns="symbol", values=col).sort_index().ffill()
    return wide


def generate_signals(context):
    """Return continuation target weights from range-expansion breakouts.

    Signal definition:
    - Compute true range and rolling ATR over the prior PARAMS.atr_window bars.
    - On the latest completed bar, flag symbols whose intraday range is at least
      PARAMS.breakout_threshold x prior ATR.
    - Go long when close is near the daily high; short when close is near the low.
    - Score by excess range multiple, gross-normalize to 1.0, and cap concentration.
    """
    output_symbols = list(context.symbols)
    symbols = [s for s in output_symbols if s in UNIVERSE]
    if len(symbols) < PARAMS.min_symbols or context.prices.empty:
        return _zero_weights(output_symbols)

    wide = _ohlc(context.prices, symbols)
    if wide is None:
        return _zero_weights(output_symbols)

    high = wide["high"].dropna(axis=1, how="any")
    low = wide["low"].reindex_like(high)
    close = wide["close"].reindex_like(high)
    open_ = wide["open"].reindex_like(high)
    tradable = [s for s in symbols if s in high.columns]
    if len(tradable) < PARAMS.min_symbols or len(high) < PARAMS.atr_window + 2:
        return _zero_weights(output_symbols)

    high = high[tradable]
    low = low[tradable]
    close = close[tradable]
    open_ = open_[tradable]

    prev_close = close.shift(1)
    true_range = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=0,
    ).groupby(level=0).max().sort_index()
    atr_prior = true_range.shift(1).rolling(PARAMS.atr_window, min_periods=PARAMS.atr_window).mean()

    latest = high.index[-1]
    range_today = (high.loc[latest] - low.loc[latest]).replace(0.0, pd.NA)
    atr = atr_prior.loc[latest].replace(0.0, pd.NA)
    close_location = ((close.loc[latest] - low.loc[latest]) / range_today).replace([float("inf"), float("-inf")], pd.NA)
    range_multiple = (range_today / atr).replace([float("inf"), float("-inf")], pd.NA)

    raw = {s: 0.0 for s in output_symbols}
    for symbol in tradable:
        loc = close_location.get(symbol)
        multiple = range_multiple.get(symbol)
        if pd.isna(loc) or pd.isna(multiple) or multiple < PARAMS.breakout_threshold:
            continue
        excess = float(multiple - PARAMS.breakout_threshold)
        # Require close near the extreme in the direction of continuation and
        # prefer bars that also close in the same direction versus open.
        if loc >= PARAMS.close_location_filter and close.loc[latest, symbol] > open_.loc[latest, symbol]:
            raw[symbol] = excess
        elif loc <= (1.0 - PARAMS.close_location_filter) and close.loc[latest, symbol] < open_.loc[latest, symbol]:
            raw[symbol] = -excess

    return _cap_and_normalize(raw, PARAMS.max_abs_weight)
