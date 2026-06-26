"""AR-086 bond ETF term-structure carry and volatility-regime allocator.

QFA contract: expose generate_signals(context) -> dict[str, float].
Uses only OHLCV bars supplied by qfa/Alpaca and never places orders.
"""

from __future__ import annotations

import math
from typing import Dict

import pandas as pd

UNIVERSE = ("SHY", "IEF", "TLT", "TIP", "LQD", "HYG", "GLD", "SPY")
BONDS = ("SHY", "IEF", "TLT", "TIP", "LQD", "HYG")
DURATION = ("IEF", "TLT", "TIP")
CREDIT = ("LQD", "HYG")
DIVERSIFIERS = ("GLD", "SPY")
MIN_HISTORY = 150
FAST = 21
MED = 63
SLOW = 126
VOL = 63
MAX_SINGLE = 0.38


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


def _dd(close: pd.DataFrame, sym: str, n: int = MED) -> float:
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
    scores = {k: max(0.0, v) for k, v in scores.items() if k in weights}
    total = sum(scores.values())
    if budget <= 0 or not scores:
        return
    if total <= 0:
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
    if len(available) < 6:
        return {s: 0.0 for s in output}

    weights = {s: 0.0 for s in output}

    # Regime: equity/credit stress reduces credit and SPY; bond volatility spike reduces long-duration.
    spy_vol = _vol(close, "SPY", FAST) or _vol(close, "SPY", VOL)
    tlt_vol = _vol(close, "TLT", VOL) or 0.14
    credit_mom = _ret(close, "HYG", MED) - _ret(close, "IEF", MED)
    equity_stress = max(0.0, min(1.0, abs(min(0.0, _dd(close, "SPY", MED))) / 0.12 + max(0.0, -credit_mom) / 0.08))
    rate_vol_stress = max(0.0, min(1.0, (tlt_vol - 0.16) / 0.14))

    # Duration carry proxy: prefer intermediate/long Treasuries when trend is positive and vol is contained.
    dur_raw = {}
    for s in DURATION:
        if s in available:
            rolldown = _ret(close, s, MED) - 0.35 * _ret(close, "SHY", MED)
            carry_trend = 0.55 * rolldown + 0.35 * _ret(close, s, SLOW) + 0.10 * _ret(close, s, FAST)
            dur_raw[s] = carry_trend - 0.55 * _vol(close, s, VOL) + 0.20 * _dd(close, s, MED)
    dur_scores = {s: max(0.0, 1.0 + z) for s, z in _z(dur_raw).items()}

    # Credit-duration relative strength: only own credit when HYG/LQD beat IEF without equity stress.
    cred_raw = {}
    for s in CREDIT:
        if s in available:
            rel = _ret(close, s, MED) - 0.65 * _ret(close, "IEF", MED) - 0.35 * _ret(close, "SPY", FAST)
            cred_raw[s] = rel + 0.25 * _ret(close, s, SLOW) - 0.70 * _vol(close, s, VOL) + 0.15 * _dd(close, s, MED)
    cred_scores = {s: max(0.0, 1.0 + z) for s, z in _z(cred_raw).items()}

    # Diversifier sleeve: GLD gets stress/negative real-rate proxy; SPY is small and only benign-regime.
    div_raw = {}
    if "GLD" in available:
        div_raw["GLD"] = 0.45 * _ret(close, "GLD", MED) + 0.20 * _ret(close, "GLD", SLOW) - 0.35 * _vol(close, "GLD", VOL) + 0.20 * equity_stress
    if "SPY" in available:
        div_raw["SPY"] = 0.25 * _ret(close, "SPY", MED) + 0.15 * _ret(close, "SPY", SLOW) - 0.70 * spy_vol - 0.60 * equity_stress
    div_scores = {s: max(0.0, 1.0 + z) for s, z in _z(div_raw).items()}

    duration_budget = 0.42 + 0.18 * equity_stress - 0.22 * rate_vol_stress
    credit_budget = 0.24 * (1.0 - 0.85 * equity_stress) * (1.0 - 0.35 * rate_vol_stress)
    div_budget = 0.18 + 0.12 * equity_stress
    shy_budget = 1.0 - max(0.0, duration_budget) - max(0.0, credit_budget) - max(0.0, div_budget)
    if shy_budget < 0.05:
        scale = 0.95 / max(duration_budget + credit_budget + div_budget, 1e-12)
        duration_budget *= scale
        credit_budget *= scale
        div_budget *= scale
        shy_budget = 0.05

    _alloc(weights, dur_scores, max(0.0, duration_budget))
    _alloc(weights, cred_scores, max(0.0, credit_budget))
    _alloc(weights, div_scores, max(0.0, div_budget))
    if "SHY" in weights:
        weights["SHY"] += max(0.0, shy_budget)

    capped = {s: max(0.0, min(MAX_SINGLE, _safe(weights.get(s, 0.0)))) for s in output}
    gross = sum(capped.values())
    if gross <= 0:
        return {s: 0.0 for s in output}
    return {s: capped[s] / gross for s in output}
