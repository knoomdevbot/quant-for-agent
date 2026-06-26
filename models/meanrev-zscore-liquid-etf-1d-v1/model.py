"""AR-002 short-horizon ETF mean-reversion alpha.

QFA contract: expose generate_signals(context) returning target weights by symbol.
The signal shorts unusually strong trailing 3-day return z-scores and buys
unusually weak trailing 3-day return z-scores, then gross-normalizes active legs.
It uses only data with timestamp <= context.as_of as supplied by the qfa backtester.
"""

from __future__ import annotations

import math


# Production/research defaults from AR-002.
UNIVERSE = ["SPY", "QQQ", "IWM", "TLT", "GLD", "SLV", "XLF", "XLK", "XLE", "XLV"]
Z_WINDOW = 20
RETURN_LOOKBACK_DAYS = 3
ENTRY_Z = 1.0
MAX_ABS_WEIGHT = 0.25
MIN_HISTORY = Z_WINDOW + RETURN_LOOKBACK_DAYS + 1


def _zero_weights(symbols):
    return {symbol: 0.0 for symbol in symbols}


def generate_signals(context):
    """Return one-day mean-reversion target weights for context.symbols.

    For each symbol, compute the latest trailing 3-day return and z-score it
    against a rolling sample of prior 3-day returns. If |z| >= ENTRY_Z, take the
    opposite sign (-z): stretched up is short; stretched down is long. Active
    weights are proportional to signal strength, capped per symbol, and
    gross-normalized by qfa downstream.
    """

    symbols = list(getattr(context, "symbols", []) or [])
    if not symbols:
        return {}

    prices = getattr(context, "prices", None)
    if prices is None or prices.empty:
        return _zero_weights(symbols)

    required_cols = {"timestamp", "symbol", "close"}
    if not required_cols.issubset(set(prices.columns)):
        return _zero_weights(symbols)

    close = (
        prices[prices["symbol"].isin(symbols)]
        .pivot(index="timestamp", columns="symbol", values="close")
        .sort_index()
        .ffill()
    )

    if close.empty:
        return _zero_weights(symbols)

    raw_scores = {}
    for symbol in symbols:
        if symbol not in close.columns:
            raw_scores[symbol] = 0.0
            continue

        series = close[symbol].dropna()
        if len(series) < MIN_HISTORY:
            raw_scores[symbol] = 0.0
            continue

        three_day_returns = series.pct_change(RETURN_LOOKBACK_DAYS).dropna()
        if len(three_day_returns) < Z_WINDOW:
            raw_scores[symbol] = 0.0
            continue

        trailing = three_day_returns.iloc[-Z_WINDOW:]
        mean = float(trailing.mean())
        std = float(trailing.std(ddof=1))
        last = float(trailing.iloc[-1])

        if not math.isfinite(std) or std <= 0.0:
            raw_scores[symbol] = 0.0
            continue

        z_score = (last - mean) / std
        if abs(z_score) < ENTRY_Z:
            raw_scores[symbol] = 0.0
        else:
            raw_scores[symbol] = -float(z_score)

    gross_score = sum(abs(value) for value in raw_scores.values())
    if gross_score <= 0.0:
        return _zero_weights(symbols)

    weights = {symbol: raw_scores.get(symbol, 0.0) / gross_score for symbol in symbols}

    # Soft concentration cap before qfa's own normalization. Re-normalize after caps.
    capped = {
        symbol: max(-MAX_ABS_WEIGHT, min(MAX_ABS_WEIGHT, float(weight)))
        for symbol, weight in weights.items()
    }
    capped_gross = sum(abs(value) for value in capped.values())
    if capped_gross <= 0.0:
        return _zero_weights(symbols)
    return {symbol: float(value / capped_gross) for symbol, value in capped.items()}
