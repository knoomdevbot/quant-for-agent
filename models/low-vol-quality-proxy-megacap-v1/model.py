"""Low-volatility quality proxy alpha for mega-cap equities.

Research-only qfa model. Exposes generate_signals(context) -> dict[symbol, weight].
No order placement or daemon usage.
"""

from __future__ import annotations

import math

import pandas as pd


UNIVERSE = (
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "META",
    "GOOGL",
    "TSLA",
    "JNJ",
    "PG",
    "KO",
    "PEP",
    "WMT",
)


class ModelParams:
    vol_window = 126
    momentum_window = 126
    momentum_filter = True
    top_n = 6
    max_abs_weight = 0.20
    min_symbols = 5
    gross_exposure = 1.0


PARAMS = ModelParams()


def _zero_weights(symbols):
    return {symbol: 0.0 for symbol in symbols}


def _cap_and_normalize_long_only(raw_scores: dict[str, float], output_symbols: list[str]) -> dict[str, float]:
    """Normalize positive scores to gross 1.0 while capping single-name weights."""
    scores = {s: max(0.0, float(raw_scores.get(s, 0.0))) for s in output_symbols}
    scores = {s: v for s, v in scores.items() if math.isfinite(v) and v > 0.0}
    if not scores:
        return _zero_weights(output_symbols)

    capped: dict[str, float] = {}
    remaining = set(scores)
    remaining_gross = float(PARAMS.gross_exposure)
    cap = float(PARAMS.max_abs_weight)

    while remaining and remaining_gross > 1e-12:
        total_score = sum(scores[s] for s in remaining)
        if total_score <= 0:
            break
        tentative = {s: remaining_gross * scores[s] / total_score for s in remaining}
        violators = {s for s, w in tentative.items() if w > cap}
        if not violators:
            capped.update(tentative)
            break
        for s in violators:
            capped[s] = cap
            remaining.remove(s)
            remaining_gross -= cap

    gross = sum(abs(v) for v in capped.values())
    if gross <= 0:
        return _zero_weights(output_symbols)
    # If the cap prevented full deployment (e.g. too few selected names), leave cash.
    scale = min(1.0, float(PARAMS.gross_exposure) / gross)
    return {s: float(capped.get(s, 0.0) * scale) for s in output_symbols}


def generate_signals(context):
    """Return long-only low-realized-volatility target weights.

    Signal construction:
    - Pivot adjusted closes for the issue universe.
    - Require at least 126 daily returns.
    - Rank names by inverse 126-day realized volatility.
    - Optional quality/defensive proxy filter: require positive 126-day total return,
      avoiding low-vol names in persistent downtrends.
    - Hold top 6 positive-score names, inverse-vol weighted, gross exposure <= 1.0,
      single-name cap 20%.
    """
    output_symbols = list(context.symbols)
    symbols = [s for s in output_symbols if s in UNIVERSE]
    if len(symbols) < PARAMS.min_symbols or context.prices is None or context.prices.empty:
        return _zero_weights(output_symbols)

    prices = context.prices.copy()
    prices["timestamp"] = pd.to_datetime(prices["timestamp"], utc=True)
    close = (
        prices[prices["symbol"].isin(symbols)]
        .pivot(index="timestamp", columns="symbol", values="close")
        .sort_index()
        .ffill()
    )
    close = close.dropna(axis=1, how="any")
    tradable = [s for s in symbols if s in close.columns]
    required_rows = max(PARAMS.vol_window, PARAMS.momentum_window) + 1
    if len(tradable) < PARAMS.min_symbols or len(close) < required_rows:
        return _zero_weights(output_symbols)

    rets = close[tradable].pct_change().tail(PARAMS.vol_window).dropna(how="all")
    realized_vol = rets.std(ddof=1).replace(0.0, pd.NA)
    inv_vol = (1.0 / realized_vol).replace([float("inf"), float("-inf")], pd.NA).dropna()

    if PARAMS.momentum_filter:
        momentum = close[tradable].iloc[-1] / close[tradable].iloc[-1 - PARAMS.momentum_window] - 1.0
        inv_vol = inv_vol[momentum.reindex(inv_vol.index) > 0.0]

    if len(inv_vol) < PARAMS.min_symbols:
        return _zero_weights(output_symbols)

    selected = inv_vol.sort_values(ascending=False).head(PARAMS.top_n)
    raw = {s: float(selected.get(s, 0.0)) for s in output_symbols}
    return _cap_and_normalize_long_only(raw, output_symbols)
