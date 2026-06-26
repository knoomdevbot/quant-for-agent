"""Cost-validated volatility-targeted ETF time-series momentum alpha.

qfa contract: expose generate_signals(context) -> dict[str, float].
The model is data-source agnostic and consumes only qfa AlphaContext.prices.
"""

from __future__ import annotations

import math

import pandas as pd

DEFAULT_PARAMS = {
    "lookback_days": 126,
    "vol_window": 20,
    "target_vol": 0.10,
    "max_abs_weight": 0.35,
    "min_periods": 127,
}


def _params(context) -> dict:
    metadata = getattr(context, "metadata", {}) or {}
    provided = metadata.get("params", {}) if isinstance(metadata, dict) else {}
    params = DEFAULT_PARAMS.copy()
    params.update({k: provided[k] for k in params.keys() & provided.keys()})
    return params


def _cap_and_renormalize(weights: dict[str, float], cap: float) -> dict[str, float]:
    if not weights:
        return weights
    capped = {symbol: max(min(value, cap), -cap) for symbol, value in weights.items()}
    gross = sum(abs(value) for value in capped.values())
    if gross <= 0:
        return {symbol: 0.0 for symbol in capped}
    return {symbol: float(value / gross) for symbol, value in capped.items()}


def generate_signals(context):
    """Positive-only medium-term ETF trend, volatility scaled and gross-normalized."""
    symbols = list(getattr(context, "symbols", []) or [])
    if not symbols:
        return {}

    params = _params(context)
    prices = getattr(context, "prices", pd.DataFrame()).copy()
    if prices.empty or "timestamp" not in prices or "symbol" not in prices or "close" not in prices:
        return {symbol: 0.0 for symbol in symbols}

    prices["timestamp"] = pd.to_datetime(prices["timestamp"], utc=True)
    close = (
        prices[prices["symbol"].isin(symbols)]
        .pivot(index="timestamp", columns="symbol", values="close")
        .sort_index()
        .ffill()
    )
    close = close.reindex(columns=symbols).dropna(how="all")
    if len(close) < int(params["min_periods"]):
        return {symbol: 0.0 for symbol in symbols}

    lookback = min(int(params["lookback_days"]), len(close) - 1)
    if lookback < 1:
        return {symbol: 0.0 for symbol in symbols}

    trailing_return = close.iloc[-1] / close.iloc[-1 - lookback] - 1.0
    returns = close.pct_change().tail(min(int(params["vol_window"]), len(close) - 1))
    realized_vol = returns.std(ddof=1) * math.sqrt(252)
    realized_vol = realized_vol.replace(0.0, pd.NA).fillna(float(params["target_vol"]))

    raw_scores: dict[str, float] = {}
    for symbol in symbols:
        mom = float(trailing_return.get(symbol, 0.0) or 0.0)
        if mom <= 0:
            raw_scores[symbol] = 0.0
            continue
        vol = float(realized_vol.get(symbol, params["target_vol"]) or params["target_vol"])
        vol_scalar = min(float(params["target_vol"]) / max(vol, 1e-8), 3.0)
        raw_scores[symbol] = mom * vol_scalar

    gross_score = sum(abs(value) for value in raw_scores.values())
    if gross_score <= 0:
        return {symbol: 0.0 for symbol in symbols}

    weights = {symbol: value / gross_score for symbol, value in raw_scores.items()}
    return _cap_and_renormalize(weights, float(params["max_abs_weight"]))
