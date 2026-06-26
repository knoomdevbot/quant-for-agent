"""AR-099 cross-asset commodity/inflation impulse allocator.

QFA contract: expose generate_signals(context) -> dict[str, float].
Uses only OHLCV bars supplied by qfa/Alpaca. Long-only, gross <= 1, no leverage.
"""

from __future__ import annotations

import math
from typing import Dict

import pandas as pd

UNIVERSE = ("DBC", "GLD", "USO", "XLE", "TIP", "TLT", "IEF", "SPY", "QQQ", "XLU")
INFLATION_HEDGES = ("DBC", "GLD", "USO", "XLE", "TIP")
DURATION = ("TLT", "IEF", "TIP")
EQUITY_RISK = ("SPY", "QQQ", "XLE")
DEFENSIVE = ("GLD", "TIP", "TLT", "IEF", "XLU")
MIN_HISTORY = 150
FAST = 5
MED = 21
SLOW = 63
LONG = 126
VOL = 63
MAX_SINGLE = 0.30


def _safe(x: float, default: float = 0.0) -> float:
    try:
        y = float(x)
    except Exception:
        return default
    return y if math.isfinite(y) else default


def _series(close: pd.DataFrame, sym: str) -> pd.Series:
    if sym not in close.columns:
        return pd.Series(dtype=float)
    return close[sym].dropna()


def _ret(close: pd.DataFrame, sym: str, n: int) -> float:
    s = _series(close, sym)
    if len(s) <= n or s.iloc[-n - 1] <= 0:
        return 0.0
    return _safe(s.iloc[-1] / s.iloc[-n - 1] - 1.0)


def _vol(close: pd.DataFrame, sym: str, n: int = VOL) -> float:
    s = _series(close, sym)
    if len(s) <= n:
        return 0.0
    r = s.pct_change().dropna().tail(n)
    return _safe(r.std() * math.sqrt(252.0))


def _dd(close: pd.DataFrame, sym: str, n: int = SLOW) -> float:
    s = _series(close, sym).tail(n)
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


def _alloc(weights: dict[str, float], scores: Dict[str, float], budget: float) -> None:
    if budget <= 0:
        return
    scores = {k: max(0.0, v) for k, v in scores.items() if k in weights}
    if not scores:
        return
    total = sum(scores.values())
    if total <= 1e-12:
        for k in scores:
            weights[k] += budget / len(scores)
    else:
        for k, v in scores.items():
            weights[k] += budget * v / total


def generate_signals(context) -> dict[str, float]:
    output = list(context.symbols)
    if context.prices is None or context.prices.empty:
        return {s: 0.0 for s in output}

    prices = context.prices.copy()
    prices["timestamp"] = pd.to_datetime(prices["timestamp"], utc=True)
    close = prices.pivot(index="timestamp", columns="symbol", values="close").sort_index().ffill()
    if len(close) < MIN_HISTORY:
        return {s: 0.0 for s in output}

    available = [s for s in output if s in UNIVERSE and s in close.columns]
    if len(available) < 7:
        return {s: 0.0 for s in output}

    weights = {s: 0.0 for s in output}

    # Inflation impulse: broad commodities/energy beating duration and equities over medium horizons.
    commodity_impulse = (
        0.35 * _ret(close, "DBC", MED)
        + 0.25 * _ret(close, "USO", MED)
        + 0.20 * _ret(close, "XLE", MED)
        + 0.20 * _ret(close, "GLD", MED)
        - 0.25 * _ret(close, "IEF", MED)
        - 0.15 * _ret(close, "SPY", FAST)
    )
    slow_inflation = (
        0.30 * _ret(close, "DBC", SLOW)
        + 0.25 * _ret(close, "XLE", SLOW)
        + 0.20 * _ret(close, "GLD", SLOW)
        + 0.25 * (_ret(close, "TIP", SLOW) - _ret(close, "IEF", SLOW))
    )
    impulse_state = max(0.0, min(1.0, (commodity_impulse + 0.55 * slow_inflation + 0.025) / 0.12))

    # Defensive confirmation: equity drawdown/volatility and utilities/duration confirmation.
    equity_dd = min(_dd(close, "SPY", SLOW), _dd(close, "QQQ", SLOW))
    risk_vol = max(_vol(close, "SPY", VOL), _vol(close, "QQQ", VOL))
    defensive_rel = 0.5 * (_ret(close, "XLU", MED) - _ret(close, "SPY", MED)) + 0.5 * (
        _ret(close, "IEF", MED) - _ret(close, "QQQ", MED)
    )
    risk_stress = max(0.0, min(1.0, abs(min(0.0, equity_dd)) / 0.16 + max(0.0, risk_vol - 0.18) / 0.22))
    defensive_confirm = max(0.0, min(1.0, risk_stress + max(0.0, defensive_rel) / 0.08))

    inflation_scores = {}
    for s in INFLATION_HEDGES:
        if s in available:
            inflation_scores[s] = (
                0.45 * _ret(close, s, MED)
                + 0.35 * _ret(close, s, SLOW)
                + 0.15 * _ret(close, s, FAST)
                - 0.30 * _vol(close, s, VOL)
                + (0.12 if s in {"GLD", "TIP"} else 0.0) * defensive_confirm
            )
    inflation_scores = {s: max(0.0, 1.0 + z) for s, z in _z(inflation_scores).items()}

    duration_scores = {}
    for s in DURATION:
        if s in available:
            duration_scores[s] = (
                0.35 * _ret(close, s, MED)
                + 0.35 * _ret(close, s, SLOW)
                + 0.20 * _ret(close, s, LONG)
                - 0.45 * _vol(close, s, VOL)
                - 0.15 * impulse_state
            )
    duration_scores = {s: max(0.0, 1.0 + z) for s, z in _z(duration_scores).items()}

    equity_scores = {}
    for s in EQUITY_RISK:
        if s in available:
            equity_scores[s] = (
                0.25 * _ret(close, s, MED)
                + 0.35 * _ret(close, s, SLOW)
                + 0.15 * _ret(close, s, LONG)
                - 0.50 * _vol(close, s, VOL)
                - 0.55 * defensive_confirm
            )
    equity_scores = {s: max(0.0, 1.0 + z) for s, z in _z(equity_scores).items()}

    defensive_scores = {}
    for s in DEFENSIVE:
        if s in available:
            defensive_scores[s] = (
                0.30 * _ret(close, s, MED)
                + 0.25 * _ret(close, s, SLOW)
                - 0.35 * _vol(close, s, VOL)
                + 0.20 * defensive_confirm
            )
    defensive_scores = {s: max(0.0, 1.0 + z) for s, z in _z(defensive_scores).items()}

    inflation_budget = 0.20 + 0.42 * impulse_state
    defensive_budget = 0.12 + 0.38 * defensive_confirm
    duration_budget = 0.16 + 0.22 * defensive_confirm - 0.18 * impulse_state
    equity_budget = 1.0 - inflation_budget - defensive_budget - max(0.0, duration_budget)
    equity_budget = max(0.05, min(0.34, equity_budget)) * (1.0 - 0.70 * defensive_confirm)

    sleeve_total = inflation_budget + defensive_budget + max(0.0, duration_budget) + max(0.0, equity_budget)
    if sleeve_total > 1.0:
        scale = 1.0 / sleeve_total
        inflation_budget *= scale
        defensive_budget *= scale
        duration_budget *= scale
        equity_budget *= scale

    _alloc(weights, inflation_scores, max(0.0, inflation_budget))
    _alloc(weights, defensive_scores, max(0.0, defensive_budget))
    _alloc(weights, duration_scores, max(0.0, duration_budget))
    _alloc(weights, equity_scores, max(0.0, equity_budget))

    capped = {s: max(0.0, min(MAX_SINGLE, _safe(weights.get(s, 0.0)))) for s in output}
    gross = sum(capped.values())
    if gross <= 1e-12:
        return {s: 0.0 for s in output}
    return {s: capped[s] / gross for s in output}
