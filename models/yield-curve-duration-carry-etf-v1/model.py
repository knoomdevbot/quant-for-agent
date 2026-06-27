"""AR-061 yield-curve duration/carry ETF allocator.

QFA contract: expose generate_signals(context) -> dict[str, float].

Research-only allocator using Alpaca/qfa daily OHLCV bars for Treasury duration
ETFs, TIPS, credit ETFs, gold, and SPY.  It intentionally differs from AR-049's
broad OHLCV carry/defensive rotation by anchoring the decision to ETF-implied
curve/duration behavior: SHY/IEF/TLT relative trends, TIP-vs-IEF inflation proxy,
and HYG-vs-LQD credit proxy.  Long-only, weekly-rebalanced, gross exposure <= 1.
"""
from __future__ import annotations

import math
from typing import Dict

import pandas as pd

UNIVERSE = ("SHY", "IEF", "TLT", "TIP", "LQD", "HYG", "GLD", "SPY")
TREASURY = ("SHY", "IEF", "TLT", "TIP")
CREDIT = ("LQD", "HYG")
HAVENS = ("GLD",)
LOOKBACK_FAST = 63
LOOKBACK_SLOW = 126
LOOKBACK_LONG = 189
VOL_WINDOW = 63
MIN_HISTORY = 210
REBALANCE_WEEKDAY = 2  # Wednesday anchor to reduce target churn.
MAX_SINGLE_WEIGHT = 0.36
MAX_CREDIT_WEIGHT = 0.16


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


def _vol(close: pd.DataFrame, symbol: str, window: int = VOL_WINDOW) -> float:
    s = _series(close, symbol)
    if len(s) <= window:
        return 0.0
    r = s.pct_change().dropna().tail(window)
    return _safe_float(r.std() * math.sqrt(252.0))


def _drawdown(close: pd.DataFrame, symbol: str, window: int) -> float:
    s = _series(close, symbol).tail(window)
    if len(s) < 2:
        return 0.0
    return _safe_float((s / s.cummax() - 1.0).iloc[-1])


def _rel(close: pd.DataFrame, long_symbol: str, short_symbol: str, window: int) -> float:
    return _ret(close, long_symbol, window) - _ret(close, short_symbol, window)


def _z_unit(x: float, scale: float) -> float:
    if scale <= 0:
        return 0.0
    return max(-1.0, min(1.0, x / scale))


def _normalize(scores: Dict[str, float], budget: float) -> Dict[str, float]:
    if budget <= 0:
        return {s: 0.0 for s in scores}
    pos = {s: max(0.0, v) for s, v in scores.items()}
    total = sum(pos.values())
    if total <= 0:
        names = list(scores)
        return {s: budget / len(names) for s in names} if names else {}
    return {s: budget * v / total for s, v in pos.items()}


def _rebalance_slice(close: pd.DataFrame) -> pd.DataFrame:
    if close.empty:
        return close
    idx = close.index
    asof = idx[-1]
    candidates = idx[(idx.weekday == REBALANCE_WEEKDAY) & (idx <= asof)]
    if len(candidates) == 0:
        return close.iloc[:1]
    return close.loc[: candidates[-1]]


def generate_signals(context) -> dict[str, float]:
    symbols = list(context.symbols)
    if context.prices is None or context.prices.empty:
        return {s: 0.0 for s in symbols}

    prices = context.prices.copy()
    prices["timestamp"] = pd.to_datetime(prices["timestamp"], utc=True)
    close_all = prices.pivot(index="timestamp", columns="symbol", values="close").sort_index().ffill()
    close = _rebalance_slice(close_all)
    if len(close) < MIN_HISTORY:
        return {s: 0.0 for s in symbols}

    available = [s for s in symbols if s in UNIVERSE and s in close.columns]
    if len(available) < 6 or not {"SHY", "IEF", "TLT"}.issubset(set(available)):
        return {s: 0.0 for s in symbols}

    # ETF-implied macro state. Positive duration_trend suggests falling-rate or
    # carry-friendly behavior; positive inflation_proxy favors TIP/GLD/shorter
    # duration; positive credit_stress favors Treasuries over corporate credit.
    duration_trend = (
        0.45 * _rel(close, "TLT", "SHY", LOOKBACK_FAST)
        + 0.35 * _rel(close, "IEF", "SHY", LOOKBACK_SLOW)
        + 0.20 * _rel(close, "TLT", "IEF", LOOKBACK_LONG)
    )
    inflation_proxy = 0.60 * _rel(close, "TIP", "IEF", LOOKBACK_SLOW) + 0.40 * _ret(close, "GLD", LOOKBACK_FAST)
    credit_stress = 0.70 * _rel(close, "LQD", "HYG", LOOKBACK_FAST) + 0.30 * _rel(close, "IEF", "HYG", LOOKBACK_FAST)
    equity_stress = max(0.0, min(1.0, abs(min(0.0, _drawdown(close, "SPY", 63))) / 0.16))
    rate_vol = 0.50 * _vol(close, "TLT", VOL_WINDOW) + 0.50 * _vol(close, "IEF", VOL_WINDOW)
    rate_vol_penalty = max(0.0, min(1.0, (rate_vol - 0.105) / 0.12))

    duration_state = max(0.0, min(1.0, 0.50 + 2.25 * duration_trend - 0.30 * rate_vol_penalty))
    inflation_state = max(0.0, min(1.0, 0.50 + 2.00 * inflation_proxy))
    stress_state = max(0.0, min(1.0, 0.55 * _z_unit(credit_stress, 0.045) + 0.45 * equity_stress))
    risk_on_credit = max(0.0, min(1.0, 0.50 - 1.80 * credit_stress + 0.80 * max(0.0, _ret(close, "SPY", LOOKBACK_FAST))))

    # Budgets emphasize duration/curve/cash rather than generic equity/commodity
    # carry.  Credit sleeve is capped and nearly off in stress; SPY is a small
    # residual risk-on anchor only when credit is calm.
    long_duration_budget = 0.12 + 0.34 * duration_state + 0.16 * stress_state
    short_duration_budget = 0.08 + 0.18 * (1.0 - duration_state) + 0.10 * rate_vol_penalty
    inflation_budget = 0.08 + 0.22 * inflation_state + 0.08 * stress_state
    credit_budget = min(0.22 * risk_on_credit * (1.0 - 0.75 * stress_state), MAX_CREDIT_WEIGHT)
    spy_budget = 0.05 * risk_on_credit * (1.0 - stress_state)
    cash_budget = 0.10 + 0.10 * rate_vol_penalty + 0.08 * max(0.0, 0.5 - duration_state)

    risky = long_duration_budget + short_duration_budget + inflation_budget + credit_budget + spy_budget
    if risky + cash_budget > 1.0:
        scale = (1.0 - cash_budget) / max(risky, 1e-12)
        long_duration_budget *= scale
        short_duration_budget *= scale
        inflation_budget *= scale
        credit_budget *= scale
        spy_budget *= scale

    weights = {s: 0.0 for s in symbols}
    duration_scores = {
        "TLT": 1.0 + 1.4 * _z_unit(_rel(close, "TLT", "SHY", LOOKBACK_FAST), 0.08) - 0.8 * _vol(close, "TLT"),
        "IEF": 1.0 + 1.1 * _z_unit(_rel(close, "IEF", "SHY", LOOKBACK_FAST), 0.05) - 0.6 * _vol(close, "IEF"),
    }
    short_scores = {"SHY": 1.0 + rate_vol_penalty, "IEF": 0.5 + 0.5 * (1.0 - rate_vol_penalty)}
    inflation_scores = {
        "TIP": 1.0 + 1.1 * _z_unit(_rel(close, "TIP", "IEF", LOOKBACK_FAST), 0.04) - 0.4 * _vol(close, "TIP"),
        "GLD": 0.7 + 0.9 * _z_unit(_ret(close, "GLD", LOOKBACK_FAST), 0.08) - 0.25 * _vol(close, "GLD"),
    }
    credit_scores = {
        "LQD": 1.0 + 0.8 * _z_unit(_rel(close, "LQD", "SHY", LOOKBACK_SLOW), 0.04) - 0.4 * _vol(close, "LQD"),
        "HYG": 0.8 + 0.8 * _z_unit(_rel(close, "HYG", "LQD", LOOKBACK_FAST), 0.05) - 0.6 * stress_state,
    }

    for sleeve in (
        _normalize({s: v for s, v in duration_scores.items() if s in available}, long_duration_budget),
        _normalize({s: v for s, v in short_scores.items() if s in available}, short_duration_budget),
        _normalize({s: v for s, v in inflation_scores.items() if s in available}, inflation_budget),
        _normalize({s: v for s, v in credit_scores.items() if s in available}, credit_budget),
        {"SPY": spy_budget} if "SPY" in available else {},
    ):
        for s, w in sleeve.items():
            if s in weights:
                weights[s] += w

    capped = {s: max(0.0, min(MAX_SINGLE_WEIGHT, _safe_float(weights.get(s, 0.0)))) for s in symbols}
    gross = sum(capped.values())
    if gross > 1.0:
        capped = {s: w / gross for s, w in capped.items()}
    return capped
