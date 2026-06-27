"""AR-101 commodity inflation-shock cross-asset ETF rotation.

QFA contract: expose generate_signals(context) -> dict[str, float].
Uses only market bars supplied by qfa/Alpaca at runtime. Long-only ETF
allocator; gross <= 1, no leverage, no orders.
"""
from __future__ import annotations

import math
from typing import Dict

import pandas as pd

UNIVERSE = (
    "SPY", "QQQ", "IWM", "XLE", "XLB", "XLI", "XLF", "XLV", "XLP", "XLU",
    "GLD", "SLV", "USO", "DBC", "DBA", "TIP", "TLT", "IEF", "SHY", "HYG", "LQD",
)
COMMODITY_LEADERS = ("USO", "DBC", "DBA", "GLD", "SLV", "XLE", "XLB")
RISK_ASSETS = ("SPY", "QQQ", "IWM", "XLI", "XLF", "HYG")
DEFENSIVE = ("GLD", "TIP", "IEF", "TLT", "XLP", "XLU", "SHY", "LQD")
DURATION = ("TLT", "IEF", "SHY", "LQD")
CYCLICAL = ("XLE", "XLB", "XLI", "XLF", "IWM")
MIN_HISTORY = 150
FAST = 5
MED = 21
SLOW = 63
LONG = 126
MAX_SINGLE = 0.25
TARGET_GROSS = 0.98


def _safe(x: float, default: float = 0.0) -> float:
    try:
        y = float(x)
    except Exception:
        return default
    return y if math.isfinite(y) else default


def _series(close: pd.DataFrame, symbol: str) -> pd.Series:
    if symbol not in close.columns:
        return pd.Series(dtype=float)
    return close[symbol].dropna()


def _ret(close: pd.DataFrame, symbol: str, n: int) -> float:
    s = _series(close, symbol)
    if len(s) <= n or s.iloc[-n - 1] <= 0:
        return 0.0
    return _safe(s.iloc[-1] / s.iloc[-n - 1] - 1.0)


def _vol(close: pd.DataFrame, symbol: str, n: int = SLOW) -> float:
    s = _series(close, symbol)
    if len(s) <= n:
        return 0.0
    return _safe(s.pct_change().dropna().tail(n).std(ddof=1) * math.sqrt(252.0))


def _dd(close: pd.DataFrame, symbol: str, n: int = SLOW) -> float:
    s = _series(close, symbol).tail(n)
    if len(s) < 2:
        return 0.0
    return _safe((s / s.cummax() - 1.0).iloc[-1])


def _z(vals: Dict[str, float]) -> Dict[str, float]:
    xs = [v for v in vals.values() if math.isfinite(v)]
    if len(xs) < 2:
        return {k: 0.0 for k in vals}
    m = sum(xs) / len(xs)
    sd = math.sqrt(sum((v - m) ** 2 for v in xs) / max(len(xs) - 1, 1))
    if sd <= 1e-12:
        return {k: 0.0 for k in vals}
    return {k: max(-3.0, min(3.0, (v - m) / sd)) for k, v in vals.items()}


def _positive(vals: Dict[str, float], floor: float = 0.03) -> Dict[str, float]:
    return {k: max(floor, 1.0 + z) for k, z in _z(vals).items()}


def _alloc(weights: dict[str, float], scores: Dict[str, float], budget: float) -> None:
    if budget <= 0:
        return
    scores = {k: max(0.0, v) for k, v in scores.items() if k in weights}
    if not scores:
        return
    total = sum(scores.values())
    for k, v in scores.items():
        weights[k] += budget * (v / total if total > 1e-12 else 1.0 / len(scores))


def generate_signals(context) -> dict[str, float]:
    symbols = list(context.symbols)
    weights = {s: 0.0 for s in symbols}
    if context.prices is None or context.prices.empty:
        return weights

    prices = context.prices.copy()
    prices["timestamp"] = pd.to_datetime(prices["timestamp"], utc=True)
    close = prices.pivot(index="timestamp", columns="symbol", values="close").sort_index().ffill()
    if len(close) < MIN_HISTORY:
        return weights

    available = [s for s in symbols if s in UNIVERSE and s in close.columns]
    if len(available) < 8:
        return weights

    # Inflation/liquidity shock state from commodity momentum, commodity dispersion,
    # credit weakness, and duration pressure. All terms are lagged close-to-close bars.
    com_avail = [s for s in COMMODITY_LEADERS if s in available]
    com_fast = sum(_ret(close, s, FAST) for s in com_avail) / max(len(com_avail), 1)
    com_med = sum(_ret(close, s, MED) for s in com_avail) / max(len(com_avail), 1)
    oil_gold_disp = _ret(close, "USO", MED) - _ret(close, "GLD", MED)
    credit_rel = _ret(close, "HYG", MED) - _ret(close, "IEF", MED)
    duration_trend = 0.55 * _ret(close, "TLT", MED) + 0.45 * _ret(close, "IEF", MED)
    equity_trend = 0.50 * _ret(close, "SPY", MED) + 0.30 * _ret(close, "QQQ", MED) + 0.20 * _ret(close, "IWM", MED)
    commodity_vol = sum(_vol(close, s, MED) / max(_vol(close, s, SLOW), 0.01) for s in com_avail) / max(len(com_avail), 1)

    inflation_shock = max(0.0, min(1.0, 4.8 * com_med + 1.8 * com_fast + 0.55 * max(0.0, commodity_vol - 1.0) - 2.0 * duration_trend))
    stagflation_stress = max(0.0, min(1.0, inflation_shock + max(0.0, -credit_rel) * 5.0 + max(0.0, -equity_trend) * 3.0))
    reflation = max(0.0, min(1.0, 3.0 * max(0.0, equity_trend) + 2.2 * max(0.0, com_med) + 1.2 * max(0.0, credit_rel)))
    duration_relief = max(0.0, min(1.0, 5.0 * max(0.0, duration_trend) + 2.0 * max(0.0, -com_med)))
    precious_stress = max(0.0, min(1.0, 4.0 * max(0.0, _ret(close, "GLD", MED)) + 0.7 * stagflation_stress - 0.8 * max(0.0, oil_gold_disp)))

    score: Dict[str, float] = {}
    for s in available:
        rv = max(_vol(close, s, SLOW), 0.01)
        mom = 0.30 * _ret(close, s, FAST) / rv + 0.45 * _ret(close, s, MED) / rv + 0.25 * _ret(close, s, SLOW) / rv
        penalty = -0.25 * max(0.0, _vol(close, s, MED) / rv - 1.2) - 0.35 * abs(min(0.0, _dd(close, s, SLOW)))
        regime = 0.0
        if s in ("USO", "DBC", "DBA", "XLE", "XLB"):
            regime += 0.70 * inflation_shock + 0.20 * reflation - 0.25 * stagflation_stress
        if s in ("GLD", "SLV", "TIP"):
            regime += 0.45 * inflation_shock + 0.40 * precious_stress + 0.20 * stagflation_stress
        if s in DURATION:
            regime += 0.55 * duration_relief + 0.35 * stagflation_stress - 0.55 * inflation_shock
        if s in ("XLP", "XLU", "XLV"):
            regime += 0.40 * stagflation_stress + 0.15 * duration_relief
        if s in RISK_ASSETS:
            regime += 0.55 * reflation - 0.45 * stagflation_stress - 0.25 * inflation_shock
        score[s] = mom + penalty + regime

    commodity_budget = 0.10 + 0.36 * inflation_shock + 0.15 * reflation - 0.10 * stagflation_stress
    precious_budget = 0.08 + 0.22 * precious_stress + 0.10 * stagflation_stress
    defensive_budget = 0.12 + 0.34 * stagflation_stress + 0.14 * duration_relief
    duration_budget = 0.08 + 0.24 * duration_relief + 0.08 * stagflation_stress - 0.20 * inflation_shock
    equity_budget = 0.20 + 0.30 * reflation - 0.26 * stagflation_stress - 0.10 * inflation_shock

    budgets = [max(0.0, commodity_budget), max(0.0, precious_budget), max(0.0, defensive_budget), max(0.0, duration_budget), max(0.02, equity_budget)]
    scale = TARGET_GROSS / max(sum(budgets), 1e-12)
    commodity_budget, precious_budget, defensive_budget, duration_budget, equity_budget = [b * scale for b in budgets]
    scores = _positive(score)
    _alloc(weights, {s: scores[s] for s in available if s in ("USO", "DBC", "DBA", "XLE", "XLB")}, commodity_budget)
    _alloc(weights, {s: scores[s] for s in available if s in ("GLD", "SLV", "TIP")}, precious_budget)
    _alloc(weights, {s: scores[s] for s in available if s in DEFENSIVE}, defensive_budget)
    _alloc(weights, {s: scores[s] for s in available if s in DURATION}, duration_budget)
    _alloc(weights, {s: scores[s] for s in available if s in RISK_ASSETS or s in ("XLV",)}, equity_budget)

    capped = {s: max(0.0, min(MAX_SINGLE, _safe(weights.get(s, 0.0)))) for s in symbols}
    gross = sum(capped.values())
    if gross > 1.0:
        capped = {s: w / gross for s, w in capped.items()}
    return capped
