"""AR-067 ETF defensive carry-surprise allocator.

QFA contract: expose generate_signals(context) -> dict[str, float].
Uses only qfa/Alpaca OHLCV bars provided in context. Long-only ETF allocator
combining medium-horizon return per downside volatility, duration carry proxies,
defensive GLD/XLU momentum, downside-volatility surprise and equity drawdown state.
"""
from __future__ import annotations

import math
from typing import Dict

import pandas as pd

UNIVERSE = ("SPY", "QQQ", "IWM", "TLT", "IEF", "SHY", "GLD", "XLU", "XLE")
RISK = ("SPY", "QQQ", "IWM", "XLE")
DURATION = ("TLT", "IEF", "SHY")
DEFENSIVE = ("TLT", "IEF", "SHY", "GLD", "XLU")
MIN_HISTORY = 130
MAX_SINGLE_WEIGHT = 0.35
REBALANCE_WEEKDAY = 2  # Wednesday anchor to reduce churn.


def _sf(x, default: float = 0.0) -> float:
    try:
        y = float(x)
    except Exception:
        return default
    return y if math.isfinite(y) else default


def _close_frame(context) -> pd.DataFrame:
    prices = context.prices
    if prices is None or prices.empty:
        return pd.DataFrame()
    p = prices.copy()
    p["timestamp"] = pd.to_datetime(p["timestamp"], utc=True)
    return p.pivot(index="timestamp", columns="symbol", values="close").sort_index().ffill()


def _rebalance_slice(close: pd.DataFrame) -> pd.DataFrame:
    if close.empty:
        return close
    idx = close.index
    asof = idx[-1]
    anchors = idx[(idx.weekday == REBALANCE_WEEKDAY) & (idx <= asof)]
    if len(anchors) == 0:
        return close.iloc[:1]
    return close.loc[: anchors[-1]]


def _series(close: pd.DataFrame, sym: str) -> pd.Series:
    if sym not in close.columns:
        return pd.Series(dtype=float)
    return close[sym].dropna()


def _ret(close: pd.DataFrame, sym: str, window: int) -> float:
    s = _series(close, sym)
    if len(s) <= window or s.iloc[-window - 1] <= 0:
        return 0.0
    return _sf(s.iloc[-1] / s.iloc[-window - 1] - 1.0)


def _down_vol(close: pd.DataFrame, sym: str, window: int) -> float:
    s = _series(close, sym)
    if len(s) <= window:
        return 0.0
    r = s.pct_change().dropna().tail(window)
    neg = r.where(r < 0.0, 0.0)
    return _sf(neg.std(ddof=1) * math.sqrt(252.0))


def _drawdown(close: pd.DataFrame, sym: str, window: int = 60) -> float:
    s = _series(close, sym).tail(window)
    if len(s) < 2:
        return 0.0
    return _sf((s / s.cummax() - 1.0).iloc[-1])


def _z(raw: Dict[str, float]) -> Dict[str, float]:
    vals = [v for v in raw.values() if math.isfinite(v)]
    if not vals:
        return {k: 0.0 for k in raw}
    mean = sum(vals) / len(vals)
    sd = math.sqrt(sum((v - mean) ** 2 for v in vals) / max(len(vals) - 1, 1))
    if sd <= 1e-12:
        return {k: 0.0 for k in raw}
    return {k: max(-2.5, min(2.5, (v - mean) / sd)) for k, v in raw.items()}


def _positive_scores(raw: Dict[str, float], floor: float = 0.05, cap: float = 2.0) -> Dict[str, float]:
    return {k: max(floor, min(cap, 1.0 + v)) for k, v in _z(raw).items()}


def _allocate(weights: Dict[str, float], scores: Dict[str, float], budget: float) -> None:
    names = [s for s, v in scores.items() if s in weights and v > 0.0]
    if budget <= 0.0 or not names:
        return
    total = sum(scores[s] for s in names)
    if total <= 0.0:
        for s in names:
            weights[s] += budget / len(names)
    else:
        for s in names:
            weights[s] += budget * scores[s] / total


def generate_signals(context) -> dict[str, float]:
    symbols = list(context.symbols)
    out = {s: 0.0 for s in symbols}
    close = _rebalance_slice(_close_frame(context))
    if len(close) < MIN_HISTORY:
        return out
    available = [s for s in symbols if s in UNIVERSE and s in close.columns]
    if len(available) < 6:
        return out

    # Equity drawdown/risk-off state: high when broad equities are under water.
    eq_dd = sum(abs(min(0.0, _drawdown(close, s, 80))) for s in ("SPY", "QQQ", "IWM") if s in available) / 3.0
    eq_r20 = sum(_ret(close, s, 20) for s in ("SPY", "QQQ", "IWM") if s in available) / 3.0
    risk_off = max(0.0, min(1.0, eq_dd / 0.12 + (0.25 if eq_r20 < -0.03 else 0.0)))

    # Defensive carry and surprise proxies from prices only.
    duration_carry = 0.55 * _ret(close, "TLT", 60) + 0.30 * _ret(close, "IEF", 60) + 0.15 * _ret(close, "SHY", 60)
    curve_stability = _ret(close, "SHY", 60) - 0.45 * _down_vol(close, "TLT", 60)
    def_mom = 0.5 * _ret(close, "GLD", 60) + 0.5 * _ret(close, "XLU", 60)
    defensive_surprise = max(-0.08, min(0.08, duration_carry + 0.5 * def_mom + 0.5 * curve_stability))

    def_budget = 0.45 + 0.30 * risk_off + (0.10 if defensive_surprise > 0 else -0.05)
    risk_budget = 0.35 * (1.0 - 0.75 * risk_off) + (0.05 if eq_r20 > 0 else 0.0)
    cash_budget = 0.10 + 0.12 * risk_off + (0.06 if defensive_surprise < 0 else 0.0)
    total = def_budget + risk_budget + cash_budget
    if total > 1.0:
        scale = (1.0 - cash_budget) / max(def_budget + risk_budget, 1e-12)
        def_budget *= scale
        risk_budget *= scale

    raw_def: Dict[str, float] = {}
    raw_risk: Dict[str, float] = {}
    for s in available:
        dv20 = _down_vol(close, s, 20) or 0.01
        dv60 = _down_vol(close, s, 60) or dv20 or 0.01
        carry = 0.45 * _ret(close, s, 20) / max(dv20, 0.015) + 0.55 * _ret(close, s, 60) / max(dv60, 0.015)
        vol_surprise = max(-0.40, min(0.40, (dv60 - dv20) / max(dv60, 0.01)))
        dd_penalty = abs(min(0.0, _drawdown(close, s, 60)))
        base = carry + 0.35 * vol_surprise - 0.20 * dd_penalty
        if s in DEFENSIVE:
            bonus = 0.30 * risk_off
            if s in DURATION:
                bonus += 0.65 * duration_carry + 0.20 * curve_stability
            if s in ("GLD", "XLU"):
                bonus += 0.55 * def_mom
            raw_def[s] = base + bonus
        elif s in RISK:
            raw_risk[s] = base - 0.55 * risk_off + 0.15 * max(0.0, eq_r20)

    _allocate(out, _positive_scores(raw_def, cap=2.2), def_budget)
    _allocate(out, _positive_scores(raw_risk, cap=1.7), risk_budget)

    capped = {s: max(0.0, min(MAX_SINGLE_WEIGHT, _sf(out.get(s, 0.0)))) for s in symbols}
    gross = sum(capped.values())
    if gross > 1.0:
        capped = {s: w / gross for s, w in capped.items()}
    return capped
