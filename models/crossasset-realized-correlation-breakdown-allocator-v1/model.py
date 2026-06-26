"""AR-080 cross-asset realized-correlation breakdown allocator.

QFA contract: expose generate_signals(context) -> dict[str, float].
Uses only qfa/Alpaca OHLCV bars supplied in context. Long-only ETF allocator
that reacts when normal stock/bond/credit/gold realized-correlation relationships
break down, with weekly rebalancing and capped gross exposure.
"""
from __future__ import annotations

import math
from typing import Dict

import pandas as pd

UNIVERSE = ("SPY", "QQQ", "TLT", "IEF", "GLD", "XLU", "XLP", "XLV", "HYG", "LQD", "SHY")
RISK = ("SPY", "QQQ", "HYG")
DEFENSIVE = ("TLT", "IEF", "GLD", "XLU", "XLP", "XLV", "LQD", "SHY")
MIN_HISTORY = 160
REBALANCE_WEEKDAY = 2  # Wednesday close signal for next session.
MAX_SINGLE_WEIGHT = 0.34


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


def _returns(close: pd.DataFrame, sym: str) -> pd.Series:
    if sym not in close.columns:
        return pd.Series(dtype=float)
    return close[sym].dropna().pct_change().dropna()


def _ret(close: pd.DataFrame, sym: str, window: int) -> float:
    if sym not in close.columns:
        return 0.0
    s = close[sym].dropna()
    if len(s) <= window or s.iloc[-window - 1] <= 0:
        return 0.0
    return _sf(s.iloc[-1] / s.iloc[-window - 1] - 1.0)


def _vol(close: pd.DataFrame, sym: str, window: int) -> float:
    r = _returns(close, sym).tail(window)
    if len(r) < max(10, window // 2):
        return 0.0
    return _sf(r.std(ddof=1) * math.sqrt(252.0))


def _corr(close: pd.DataFrame, a: str, b: str, window: int) -> float:
    if a not in close.columns or b not in close.columns:
        return 0.0
    pair = close[[a, b]].dropna().pct_change().dropna().tail(window)
    if len(pair) < max(12, window // 2):
        return 0.0
    return _sf(pair[a].corr(pair[b]))


def _corr_z(close: pd.DataFrame, a: str, b: str, short: int = 21, base: int = 126) -> float:
    if a not in close.columns or b not in close.columns:
        return 0.0
    pair = close[[a, b]].dropna().pct_change().dropna()
    if len(pair) < base + short:
        return 0.0
    rolling = pair[a].rolling(short).corr(pair[b]).dropna().tail(base)
    if len(rolling) < 40:
        return 0.0
    sd = rolling.std(ddof=1)
    if not math.isfinite(sd) or sd <= 1e-12:
        return 0.0
    return max(-3.0, min(3.0, _sf((rolling.iloc[-1] - rolling.mean()) / sd)))


def _drawdown(close: pd.DataFrame, sym: str, window: int) -> float:
    if sym not in close.columns:
        return 0.0
    s = close[sym].dropna().tail(window)
    if len(s) < 2:
        return 0.0
    return _sf((s / s.cummax() - 1.0).iloc[-1])


def _z_scores(raw: Dict[str, float]) -> Dict[str, float]:
    vals = [v for v in raw.values() if math.isfinite(v)]
    if not vals:
        return {k: 0.0 for k in raw}
    mean = sum(vals) / len(vals)
    sd = math.sqrt(sum((v - mean) ** 2 for v in vals) / max(1, len(vals) - 1))
    if sd <= 1e-12:
        return {k: 0.0 for k in raw}
    return {k: max(-2.5, min(2.5, (v - mean) / sd)) for k, v in raw.items()}


def _allocate(out: Dict[str, float], scores: Dict[str, float], budget: float) -> None:
    if budget <= 0:
        return
    pos = {s: max(0.05, 1.0 + z) for s, z in _z_scores(scores).items() if s in out}
    total = sum(pos.values())
    if total <= 0:
        return
    for s, score in pos.items():
        out[s] += budget * score / total


def generate_signals(context) -> dict[str, float]:
    symbols = list(context.symbols)
    out = {s: 0.0 for s in symbols}
    close = _rebalance_slice(_close_frame(context))
    if len(close) < MIN_HISTORY:
        return out
    available = [s for s in symbols if s in UNIVERSE and s in close.columns]
    if len(available) < 7 or "SPY" not in available or "IEF" not in available:
        return out

    # Breakdown score rises when diversifiers stop diversifying or credit trades like equity.
    sb_z = _corr_z(close, "SPY", "IEF", 21, 126)
    stlt_z = _corr_z(close, "SPY", "TLT", 21, 126)
    ce_z = _corr_z(close, "SPY", "HYG", 21, 126)
    ge_z = _corr_z(close, "SPY", "GLD", 21, 126)
    sb_corr = 0.5 * _corr(close, "SPY", "IEF", 21) + 0.5 * _corr(close, "SPY", "TLT", 21)
    credit_corr = _corr(close, "SPY", "HYG", 21)
    gold_corr = _corr(close, "SPY", "GLD", 21)
    eq_vol = 0.5 * _vol(close, "SPY", 21) + 0.5 * _vol(close, "QQQ", 21)
    eq_dd = abs(min(0.0, 0.5 * _drawdown(close, "SPY", 63) + 0.5 * _drawdown(close, "QQQ", 63)))
    breadth = sum(1 for s in ("SPY", "QQQ", "XLU", "XLP", "XLV", "HYG") if _ret(close, s, 63) > 0.0) / 6.0

    breakdown = 0.0
    breakdown += max(0.0, sb_z - 0.35) / 2.2
    breakdown += max(0.0, stlt_z - 0.35) / 2.5
    breakdown += max(0.0, ce_z - 0.60) / 2.4
    breakdown += max(0.0, ge_z - 0.20) / 2.4
    breakdown += max(0.0, sb_corr - 0.15) / 0.75
    breakdown += max(0.0, gold_corr - 0.10) / 0.75
    breakdown += max(0.0, eq_vol - 0.20) / 0.35
    breakdown += max(0.0, eq_dd - 0.05) / 0.18
    breakdown = max(0.0, min(1.0, breakdown / 3.0))

    benign = max(0.0, min(1.0, (breadth - 0.35) / 0.50 + (0.15 if _ret(close, "SPY", 63) > 0 else 0.0)))
    risk_budget = max(0.08, min(0.48, 0.42 * benign * (1.0 - 0.80 * breakdown)))
    defensive_budget = max(0.34, min(0.78, 0.42 + 0.34 * breakdown + 0.08 * (1.0 - benign)))
    cash_budget = max(0.04, min(0.32, 1.0 - risk_budget - defensive_budget))
    if risk_budget + defensive_budget + cash_budget > 1.0:
        scale = (1.0 - cash_budget) / max(risk_budget + defensive_budget, 1e-12)
        risk_budget *= scale
        defensive_budget *= scale

    risk_scores: Dict[str, float] = {}
    defensive_scores: Dict[str, float] = {}
    for s in available:
        mom = 0.60 * _ret(close, s, 63) + 0.40 * _ret(close, s, 21)
        rv = max(_vol(close, s, 21), 0.035)
        carry_score = mom / rv
        dd_penalty = abs(min(0.0, _drawdown(close, s, 63)))
        if s in RISK:
            risk_scores[s] = carry_score - 1.4 * breakdown - 0.5 * dd_penalty + 0.25 * (credit_corr < 0.75)
        elif s in DEFENSIVE:
            diversifier_bonus = 0.0
            if s in ("IEF", "TLT"):
                diversifier_bonus = 0.45 * max(0.0, -sb_corr) + 0.25 * _ret(close, s, 63)
            elif s == "GLD":
                diversifier_bonus = 0.50 * max(0.0, -gold_corr) + 0.35 * _ret(close, s, 63)
            elif s in ("XLU", "XLP", "XLV"):
                diversifier_bonus = 0.18 * max(0.0, 1.0 - eq_vol / 0.30)
            elif s == "LQD":
                diversifier_bonus = 0.20 * max(0.0, 1.0 - credit_corr)
            elif s == "SHY":
                diversifier_bonus = 0.35 * breakdown
            defensive_scores[s] = 0.45 * carry_score + diversifier_bonus + 0.75 * breakdown - 0.25 * dd_penalty

    _allocate(out, risk_scores, risk_budget)
    _allocate(out, defensive_scores, defensive_budget)
    if "SHY" in out:
        out["SHY"] += cash_budget

    capped = {s: max(0.0, min(MAX_SINGLE_WEIGHT, _sf(out.get(s, 0.0)))) for s in symbols}
    gross = sum(capped.values())
    if gross > 1.0:
        capped = {s: w / gross for s, w in capped.items()}
    return capped
