"""AR-097 commodity/inflation-shock ETF rotation.

QFA contract: expose generate_signals(context) -> dict[str, float].

Mechanism: use only daily OHLCV supplied by qfa/Alpaca to identify broad
commodity/inflation and risk shocks, then rotate among commodity proxies,
inflation-sensitive assets, duration, and defensive equity sectors.  This is
intentionally a macro/commodity daily allocation idea, not an intraday opening
range/liquidity reversal refinement of rejected AR-085.
"""
from __future__ import annotations

import math
from typing import Dict

import pandas as pd

UNIVERSE = ("GLD", "USO", "DBC", "XLE", "TIP", "TLT", "IEF", "SPY", "XLP", "XLU")
COMMODITY = ("USO", "DBC", "XLE")
DEFENSIVE = ("GLD", "TIP", "IEF", "TLT", "XLP", "XLU")
EQUITY_DEF = ("XLP", "XLU")
DURATION = ("TLT", "IEF")
MIN_HISTORY = 90
REBALANCE_WEEKDAY = 2  # Wednesday anchor to reduce churn while remaining daily-compatible.
MAX_SINGLE_WEIGHT = 0.30
TARGET_GROSS_NORMAL = 0.95
TARGET_GROSS_STRESS = 0.85


def _safe_float(value, default: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return default
    return out if math.isfinite(out) else default


def _close_matrix(context) -> pd.DataFrame:
    if context.prices is None or context.prices.empty:
        return pd.DataFrame()
    prices = context.prices.copy()
    prices["timestamp"] = pd.to_datetime(prices["timestamp"], utc=True)
    return prices.pivot(index="timestamp", columns="symbol", values="close").sort_index().ffill()


def _rebalance_slice(close: pd.DataFrame) -> pd.DataFrame:
    if close.empty:
        return close
    idx = close.index
    asof = idx[-1]
    anchors = idx[(idx.weekday == REBALANCE_WEEKDAY) & (idx <= asof)]
    if len(anchors) == 0:
        return close.iloc[:1]
    return close.loc[: anchors[-1]]


def _series(close: pd.DataFrame, symbol: str) -> pd.Series:
    if symbol not in close.columns:
        return pd.Series(dtype=float)
    return close[symbol].dropna()


def _ret(close: pd.DataFrame, symbol: str, window: int) -> float:
    s = _series(close, symbol)
    if len(s) <= window or s.iloc[-window - 1] <= 0:
        return 0.0
    return _safe_float(s.iloc[-1] / s.iloc[-window - 1] - 1.0)


def _vol(close: pd.DataFrame, symbol: str, window: int) -> float:
    s = _series(close, symbol)
    if len(s) <= window:
        return 0.0
    return _safe_float(s.pct_change().dropna().tail(window).std(ddof=1) * math.sqrt(252.0))


def _drawdown(close: pd.DataFrame, symbol: str, window: int = 60) -> float:
    s = _series(close, symbol).tail(window)
    if len(s) < 2:
        return 0.0
    peak = s.cummax()
    return _safe_float((s / peak - 1.0).iloc[-1])


def _zscore(values: Dict[str, float]) -> Dict[str, float]:
    vals = [v for v in values.values() if math.isfinite(v)]
    if not vals:
        return {k: 0.0 for k in values}
    mean = sum(vals) / len(vals)
    var = sum((v - mean) ** 2 for v in vals) / max(len(vals) - 1, 1)
    sd = math.sqrt(var)
    if sd <= 1e-12:
        return {k: 0.0 for k in values}
    return {k: max(-3.0, min(3.0, (v - mean) / sd)) for k, v in values.items()}


def _positive_scores(raw: Dict[str, float], floor: float = 0.05, cap: float = 2.5) -> Dict[str, float]:
    return {s: max(floor, min(cap, 1.0 + z)) for s, z in _zscore(raw).items()}


def _add_bucket(weights: Dict[str, float], scores: Dict[str, float], budget: float) -> None:
    names = [s for s, v in scores.items() if s in weights and v > 0]
    if budget <= 0 or not names:
        return
    total = sum(scores[s] for s in names)
    if total <= 0:
        for s in names:
            weights[s] += budget / len(names)
    else:
        for s in names:
            weights[s] += budget * scores[s] / total


def generate_signals(context) -> dict[str, float]:
    output_symbols = list(context.symbols)
    weights = {s: 0.0 for s in output_symbols}
    close_all = _close_matrix(context)
    close = _rebalance_slice(close_all)
    if len(close) < MIN_HISTORY:
        return weights

    available = [s for s in output_symbols if s in UNIVERSE and s in close.columns]
    if len(available) < 6:
        return weights

    # Cross-asset shock state. Commodity trend/vol confirmation distinguishes
    # inflation shock from generic equity stress.
    commodity_trend = sum(_ret(close, s, 20) for s in COMMODITY if s in available) / max(
        sum(1 for s in COMMODITY if s in available), 1
    )
    commodity_vol_ratio = sum((_vol(close, s, 20) / max(_vol(close, s, 60), 0.01)) for s in COMMODITY if s in available) / max(
        sum(1 for s in COMMODITY if s in available), 1
    )
    duration_trend = 0.5 * (_ret(close, "IEF", 20) + _ret(close, "TLT", 20))
    tip_confirm = _ret(close, "TIP", 20) - _ret(close, "IEF", 20)
    spy_dd = _drawdown(close, "SPY", 60)
    spy_trend = _ret(close, "SPY", 20)
    gld_trend = _ret(close, "GLD", 20)

    inflation_shock = max(0.0, min(1.0, 7.5 * commodity_trend + 0.9 * max(0.0, commodity_vol_ratio - 1.0) + 5.0 * tip_confirm))
    risk_shock = max(0.0, min(1.0, -10.0 * min(0.0, spy_trend) + -5.0 * min(0.0, spy_dd + 0.03)))
    duration_pressure = max(0.0, min(1.0, -8.0 * duration_trend + 0.5 * inflation_shock))
    reflation_relief = max(0.0, min(1.0, 4.0 * max(0.0, spy_trend) + 3.0 * max(0.0, commodity_trend)))

    raw: Dict[str, float] = {}
    for s in available:
        rv20 = max(_vol(close, s, 20), 0.01)
        rv60 = max(_vol(close, s, 60), rv20, 0.01)
        trend_score = 0.55 * _ret(close, s, 20) / rv20 + 0.45 * _ret(close, s, 60) / rv60
        vol_penalty = -0.25 * max(0.0, rv20 / rv60 - 1.15)
        dd_penalty = -0.35 * abs(min(0.0, _drawdown(close, s, 60)))
        shock_bonus = 0.0
        if s in COMMODITY:
            shock_bonus += 0.55 * inflation_shock - 0.25 * risk_shock
        if s == "GLD":
            shock_bonus += 0.35 * max(inflation_shock, risk_shock) + 0.20 * max(0.0, gld_trend)
        if s == "TIP":
            shock_bonus += 0.30 * inflation_shock - 0.10 * duration_pressure
        if s in DURATION:
            shock_bonus += 0.45 * risk_shock - 0.45 * inflation_shock - 0.25 * duration_pressure
        if s in EQUITY_DEF:
            shock_bonus += 0.25 * risk_shock + 0.10 * reflation_relief
        if s == "SPY":
            shock_bonus += 0.25 * reflation_relief - 0.35 * risk_shock - 0.20 * inflation_shock
        raw[s] = trend_score + vol_penalty + dd_penalty + shock_bonus

    # Regime budgets remain long-only, gross <= 1, with cash held during unresolved stress.
    commodity_budget = 0.18 + 0.30 * inflation_shock + 0.12 * reflation_relief - 0.15 * risk_shock
    defensive_budget = 0.32 + 0.24 * risk_shock + 0.10 * inflation_shock
    equity_budget = 0.18 + 0.20 * reflation_relief - 0.18 * risk_shock - 0.10 * inflation_shock
    target_gross = TARGET_GROSS_STRESS if max(inflation_shock, risk_shock) > 0.55 else TARGET_GROSS_NORMAL
    commodity_budget = max(0.05, commodity_budget)
    defensive_budget = max(0.15, defensive_budget)
    equity_budget = max(0.0, equity_budget)
    scale = target_gross / max(commodity_budget + defensive_budget + equity_budget, 1e-12)

    scores = _positive_scores(raw)
    _add_bucket(weights, {s: scores[s] for s in available if s in COMMODITY}, commodity_budget * scale)
    _add_bucket(weights, {s: scores[s] for s in available if s in DEFENSIVE}, defensive_budget * scale)
    _add_bucket(weights, {s: scores[s] for s in available if s == "SPY"}, equity_budget * scale)

    capped = {s: max(0.0, min(MAX_SINGLE_WEIGHT, _safe_float(weights.get(s, 0.0)))) for s in output_symbols}
    gross = sum(capped.values())
    if gross > 1.0:
        capped = {s: w / gross for s, w in capped.items()}
    return capped
