"""Cross-sectional defensive ETF rotation alpha for qfa.

QFA contract: expose generate_signals(context) -> dict[str, float].
The model is research-only, consumes only context.prices OHLCV bars, and never
places orders. It differs from single-asset TSMOM by ranking ETFs against one
another and rotating between growth/cyclical and defensive baskets.
"""

from __future__ import annotations

import math

import pandas as pd


DEFAULT_PARAMS = {
    "short_lookback": 63,
    "long_lookback": 126,
    "vol_window": 20,
    "min_periods": 127,
    "top_n": 3,
    "target_vol": 0.10,
    "max_abs_weight": 0.50,
    "risk_on_symbols": ("SPY", "QQQ", "IWM", "XLV", "XLY", "XLE"),
    "defensive_symbols": ("XLU", "XLP", "TLT", "IEF", "GLD"),
}


def _params(context) -> dict:
    metadata = getattr(context, "metadata", {}) or {}
    provided = metadata.get("params", {}) if isinstance(metadata, dict) else {}
    params = DEFAULT_PARAMS.copy()
    params.update({k: provided[k] for k in params.keys() & provided.keys()})
    return params


def _gross_normalize(weights: dict[str, float]) -> dict[str, float]:
    gross = sum(abs(v) for v in weights.values())
    if gross <= 0:
        return {symbol: 0.0 for symbol in weights}
    return {symbol: float(v / gross) for symbol, v in weights.items()}


def _cap_and_renormalize(weights: dict[str, float], cap: float) -> dict[str, float]:
    if not weights:
        return {}
    capped = {symbol: max(min(float(value), cap), -cap) for symbol, value in weights.items()}
    return _gross_normalize(capped)


def generate_signals(context):
    """Return long-only cross-sectional ETF rotation weights.

    Daily process:
    - rank ETFs by blended 63-day and 126-day return, penalized by 20-day vol;
    - choose risk-on basket only when its median cross-sectional score exceeds
      the defensive basket and SPY's blended momentum is positive;
    - otherwise rotate into defensive ETF winners; and
    - allocate across top-ranked ETFs with inverse-volatility scaling.
    """
    symbols = list(getattr(context, "symbols", []) or [])
    if not symbols:
        return {}

    params = _params(context)
    prices = getattr(context, "prices", pd.DataFrame()).copy()
    required = {"timestamp", "symbol", "close"}
    if prices.empty or not required.issubset(prices.columns):
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

    short_lb = min(int(params["short_lookback"]), len(close) - 1)
    long_lb = min(int(params["long_lookback"]), len(close) - 1)
    vol_window = min(int(params["vol_window"]), len(close) - 1)
    if min(short_lb, long_lb, vol_window) < 2:
        return {symbol: 0.0 for symbol in symbols}

    returns = close.pct_change()
    ret_short = close.iloc[-1] / close.iloc[-1 - short_lb] - 1.0
    ret_long = close.iloc[-1] / close.iloc[-1 - long_lb] - 1.0
    realized_vol = (returns.tail(vol_window).std(ddof=1) * math.sqrt(252)).replace(0.0, pd.NA)
    realized_vol = realized_vol.fillna(float(params["target_vol"]))

    blended_momentum = 0.60 * ret_short + 0.40 * ret_long
    vol_penalty = realized_vol.clip(lower=0.05)
    score = (blended_momentum / vol_penalty).replace([float("inf"), float("-inf")], pd.NA).dropna()

    risk_on = [s for s in params["risk_on_symbols"] if s in symbols and s in score.index]
    defensive = [s for s in params["defensive_symbols"] if s in symbols and s in score.index]
    weights = {symbol: 0.0 for symbol in symbols}
    if not risk_on or not defensive:
        return weights

    risk_on_median = float(score.reindex(risk_on).dropna().median())
    defensive_median = float(score.reindex(defensive).dropna().median())
    spy_momentum = float(blended_momentum.get("SPY", 0.0) or 0.0)

    if risk_on_median > defensive_median and spy_momentum > 0.0:
        candidate_symbols = risk_on
    else:
        candidate_symbols = defensive

    ranked = score.reindex(candidate_symbols).dropna().sort_values(ascending=False)
    top_n = max(1, int(params["top_n"]))
    selected = list(ranked.head(top_n).index)
    if not selected:
        selected = candidate_symbols[:top_n]

    raw: dict[str, float] = {}
    for symbol in selected:
        positive_score = max(float(score.get(symbol, 0.0) or 0.0), 0.0)
        vol = float(realized_vol.get(symbol, params["target_vol"]) or params["target_vol"])
        inv_vol_scale = min(float(params["target_vol"]) / max(vol, 1e-8), 3.0)
        raw[symbol] = (positive_score + 0.01) * inv_vol_scale

    if sum(abs(v) for v in raw.values()) <= 0.0:
        raw = {symbol: 1.0 for symbol in selected}

    weights.update(_cap_and_renormalize(raw, float(params["max_abs_weight"])))
    return weights
