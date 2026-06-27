"""Cross-sectional intermediate momentum alpha for liquid mega-cap equities.

QFA contract: expose generate_signals(context) -> dict[symbol, weight].
The model is research-only and never places orders.
"""

from __future__ import annotations

import math

import pandas as pd


class ModelParams:
    lookback_days = 63
    skip_days = 5
    volatility_normalize = True
    volatility_window = 20
    max_abs_weight = 0.25
    min_symbols = 3


PARAMS = ModelParams()
UNIVERSE = ("AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA")


def _zero_weights(symbols):
    return {symbol: 0.0 for symbol in symbols}


def _cap_and_normalize(weights: dict[str, float], max_abs_weight: float) -> dict[str, float]:
    """Cap absolute weights while preserving gross exposure where feasible."""
    clean = {s: float(w) for s, w in weights.items() if math.isfinite(float(w))}
    if not clean or sum(abs(w) for w in clean.values()) == 0:
        return {s: 0.0 for s in weights}

    signs = {s: 1.0 if w >= 0 else -1.0 for s, w in clean.items()}
    magnitudes = {s: abs(w) for s, w in clean.items()}
    capped: dict[str, float] = {}
    remaining = set(magnitudes)
    remaining_gross = 1.0

    # Water-fill by absolute signal strength: fix names that exceed the cap and
    # rescale the rest to the remaining gross budget.
    while remaining:
        total_mag = sum(magnitudes[s] for s in remaining)
        if total_mag == 0 or remaining_gross <= 0:
            break
        tentative = {s: remaining_gross * magnitudes[s] / total_mag for s in remaining}
        violators = {s for s, mag in tentative.items() if mag > max_abs_weight}
        if not violators:
            capped.update(tentative)
            break
        for s in violators:
            capped[s] = max_abs_weight
            remaining.remove(s)
            remaining_gross -= max_abs_weight

    if not capped:
        return {s: 0.0 for s in weights}
    return {s: float(signs.get(s, 1.0) * capped.get(s, 0.0)) for s in weights}


def generate_signals(context):
    """Return cross-sectional long/short target weights by symbol.

    Signal: 63-trading-day total return ending 5 sessions before `as_of`, optionally
    divided by recent realized volatility. Scores are demeaned cross-sectionally and
    gross-normalized to 1.0 with a single-name cap.
    """
    symbols = [s for s in context.symbols if s in UNIVERSE]
    output_symbols = list(context.symbols)
    if len(symbols) < PARAMS.min_symbols:
        return _zero_weights(output_symbols)

    prices = context.prices.copy()
    if prices.empty:
        return _zero_weights(output_symbols)
    prices["timestamp"] = pd.to_datetime(prices["timestamp"], utc=True)
    close = (
        prices[prices["symbol"].isin(symbols)]
        .pivot(index="timestamp", columns="symbol", values="close")
        .sort_index()
        .ffill()
    )
    close = close.dropna(axis=1, how="any")
    tradable = [s for s in symbols if s in close.columns]
    required_rows = PARAMS.lookback_days + PARAMS.skip_days + 1
    if len(tradable) < PARAMS.min_symbols or len(close) < required_rows:
        return _zero_weights(output_symbols)

    current_idx = -1 - PARAMS.skip_days
    past_idx = current_idx - PARAMS.lookback_days
    current = close.iloc[current_idx]
    past = close.iloc[past_idx]
    momentum = current / past - 1.0

    if PARAMS.volatility_normalize:
        rets = close[tradable].pct_change().iloc[current_idx - PARAMS.volatility_window + 1 : current_idx + 1]
        vol = rets.std().replace(0.0, pd.NA)
        momentum = momentum / vol

    scores = momentum.replace([float("inf"), float("-inf")], pd.NA).dropna()
    scores = scores[[s for s in tradable if s in scores.index]]
    if len(scores) < PARAMS.min_symbols or float(scores.std(ddof=0)) == 0.0:
        return _zero_weights(output_symbols)

    demeaned = scores - scores.mean()
    raw = {s: float(demeaned.get(s, 0.0)) for s in output_symbols}
    return _cap_and_normalize(raw, PARAMS.max_abs_weight)
