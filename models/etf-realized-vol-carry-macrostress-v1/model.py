"""AR-066 ETF realized-volatility carry rotation after macro-stress regimes.

QFA contract: expose generate_signals(context) -> dict[str, float].

Mechanism: after broad cross-ETF downside-volatility stress starts to dissipate, allocate
long-only toward ETFs with positive medium-horizon return per downside volatility and
supportive defensive carry (SHY/TLT/GLD behavior).  The model intentionally avoids
macro-calendar terms and the next-day laggard reversal structure rejected in AR-053.
It uses only OHLCV bars supplied by qfa/Alpaca.
"""
from __future__ import annotations

import math
from typing import Dict, Iterable

import pandas as pd

UNIVERSE = ("SPY", "QQQ", "IWM", "TLT", "GLD", "XLU", "XLE", "SHY")
RISK_ETFS = ("SPY", "QQQ", "IWM", "XLE")
DEFENSIVE_ETFS = ("TLT", "GLD", "XLU", "SHY")
VOL_WINDOWS = (20, 60)
RETURN_WINDOWS = (20, 60)
MIN_HISTORY = 90
MAX_SINGLE_WEIGHT = 0.35
REBALANCE_WEEKDAY = 2  # Wednesday anchor to lower churn.


def _safe_float(value, default: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return default
    return out if math.isfinite(out) else default


def _series(close: pd.DataFrame, symbol: str) -> pd.Series:
    if symbol not in close.columns:
        return pd.Series(dtype=float)
    return close[symbol].dropna()


def _ret(close: pd.DataFrame, symbol: str, window: int) -> float:
    s = _series(close, symbol)
    if len(s) <= window or s.iloc[-window - 1] <= 0:
        return 0.0
    return _safe_float(s.iloc[-1] / s.iloc[-window - 1] - 1.0)


def _downside_vol(close: pd.DataFrame, symbol: str, window: int) -> float:
    s = _series(close, symbol)
    if len(s) <= window:
        return 0.0
    r = s.pct_change().dropna().tail(window)
    neg = r.where(r < 0.0, 0.0)
    # Include zeros so calm periods are rewarded but sparse negatives do not explode.
    return _safe_float(neg.std() * math.sqrt(252.0))


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


def _rank_scores(raw: Dict[str, float], floor: float = 0.05, cap: float = 2.0) -> Dict[str, float]:
    return {s: max(floor, min(cap, 1.0 + z)) for s, z in _zscore(raw).items()}


def _rebalance_slice(close: pd.DataFrame) -> pd.DataFrame:
    if close.empty:
        return close
    idx = close.index
    asof = idx[-1]
    candidates = idx[(idx.weekday == REBALANCE_WEEKDAY) & (idx <= asof)]
    if len(candidates) == 0:
        return close.iloc[:1]
    return close.loc[: candidates[-1]]


def _stress_breadth(close: pd.DataFrame, symbols: Iterable[str]) -> tuple[float, float]:
    flags = []
    recovery_flags = []
    for s in symbols:
        if s not in close.columns:
            continue
        r20 = _ret(close, s, 20)
        r60 = _ret(close, s, 60)
        dv20 = _downside_vol(close, s, 20)
        dv60 = _downside_vol(close, s, 60) or dv20 or 1e-6
        dd60 = _drawdown(close, s, 60)
        flags.append(1.0 if (dv20 > 1.15 * dv60 and r20 < 0.0) or dd60 < -0.065 else 0.0)
        recovery_flags.append(1.0 if (r20 > 0.0 and r60 < 0.04 and dd60 > -0.10) else 0.0)
    breadth = sum(flags) / max(len(flags), 1)
    recovery = sum(recovery_flags) / max(len(recovery_flags), 1)
    return _safe_float(breadth), _safe_float(recovery)


def _allocate(weights: Dict[str, float], scores: Dict[str, float], budget: float) -> None:
    names = [s for s, v in scores.items() if s in weights and v > 0]
    if budget <= 0 or not names:
        return
    total = sum(scores[s] for s in names)
    if total <= 0:
        for s in names:
            weights[s] += budget / len(names)
        return
    for s in names:
        weights[s] += budget * scores[s] / total


def generate_signals(context) -> dict[str, float]:
    output_symbols = list(context.symbols)
    if context.prices is None or context.prices.empty:
        return {s: 0.0 for s in output_symbols}

    prices = context.prices.copy()
    prices["timestamp"] = pd.to_datetime(prices["timestamp"], utc=True)
    close_all = prices.pivot(index="timestamp", columns="symbol", values="close").sort_index().ffill()
    close = _rebalance_slice(close_all)
    if len(close) < MIN_HISTORY:
        return {s: 0.0 for s in output_symbols}

    available = [s for s in output_symbols if s in UNIVERSE and s in close.columns]
    if len(available) < 5:
        return {s: 0.0 for s in output_symbols}

    stress, recovery = _stress_breadth(close, available)
    post_stress = max(0.0, min(1.0, 0.65 * recovery + 0.35 * max(0.0, 0.60 - stress) / 0.60))
    defensive_pressure = max(0.0, min(1.0, stress * (1.0 - 0.50 * recovery)))

    shy_carry = _ret(close, "SHY", 60) - 0.15 * _downside_vol(close, "SHY", 60)
    tlt_gld_carry = 0.5 * (_ret(close, "TLT", 60) + _ret(close, "GLD", 60)) - 0.25 * (
        _downside_vol(close, "TLT", 60) + _downside_vol(close, "GLD", 60)
    )
    defensive_carry = max(-0.05, min(0.05, shy_carry + 0.5 * tlt_gld_carry))

    risk_budget = 0.12 + 0.30 * post_stress * (1.0 - defensive_pressure)
    defensive_budget = 0.38 + 0.22 * defensive_pressure + (0.08 if defensive_carry > 0 else 0.0)
    residual_cash = 0.18 + 0.10 * stress
    total = risk_budget + defensive_budget + residual_cash
    if total > 1.0:
        scale = (1.0 - residual_cash) / max(risk_budget + defensive_budget, 1e-12)
        risk_budget *= scale
        defensive_budget *= scale

    weights = {s: 0.0 for s in output_symbols}
    raw_risk: Dict[str, float] = {}
    raw_def: Dict[str, float] = {}
    for s in available:
        rv20 = _downside_vol(close, s, 20) or 0.01
        rv60 = _downside_vol(close, s, 60) or rv20 or 0.01
        carry = 0.55 * _ret(close, s, 20) / max(rv20, 0.01) + 0.45 * _ret(close, s, 60) / max(rv60, 0.01)
        recovery_bonus = 0.25 * max(0.0, _ret(close, s, 20)) - 0.20 * abs(min(0.0, _drawdown(close, s, 60)))
        vol_calm = -0.35 * max(0.0, rv20 - rv60)
        score = carry + recovery_bonus + vol_calm
        if s in RISK_ETFS:
            raw_risk[s] = score - 0.35 * stress - 0.15 * max(0.0, rv20 - 0.22)
        elif s in DEFENSIVE_ETFS:
            raw_def[s] = score + 0.25 * stress + (0.20 if s in ("SHY", "TLT", "GLD") and defensive_carry > 0 else 0.0)

    _allocate(weights, _rank_scores(raw_risk, cap=1.8), risk_budget)
    _allocate(weights, _rank_scores(raw_def, cap=2.0), defensive_budget)

    capped = {s: max(0.0, min(MAX_SINGLE_WEIGHT, _safe_float(weights.get(s, 0.0)))) for s in output_symbols}
    gross = sum(capped.values())
    if gross > 1.0:
        capped = {s: w / gross for s, w in capped.items()}
    return capped
