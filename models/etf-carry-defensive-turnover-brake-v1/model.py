"""AR-060 lower-turnover orthogonal ETF carry/defensive allocation.

QFA contract: expose generate_signals(context) -> dict[str, float].

This refines AR-049 by (1) anchoring features to a weekly rebalance date so
qfa sees stable target weights between rebalances, (2) using slower 63/126/189d
carry/defensive ranks, and (3) explicitly penalizing SPY/QQQ/IWM trend-beta and
holding residual cash.  It uses only OHLCV bars supplied by qfa/Alpaca.
"""
from __future__ import annotations

import math
from typing import Dict

import pandas as pd

UNIVERSE = ("SPY", "QQQ", "IWM", "TLT", "IEF", "GLD", "USO", "FXE", "FXY", "UUP")
EQUITIES = ("SPY", "QQQ", "IWM")
DURATION = ("TLT", "IEF")
HAVENS = ("GLD", "UUP", "FXY")
CARRY = ("GLD", "USO", "FXE", "FXY", "UUP")
LOOKBACKS = (63, 126, 189)
VOL_WINDOW = 126
FAST_WINDOW = 21
MIN_HISTORY = 210
MAX_SINGLE_WEIGHT = 0.30
REBALANCE_WEEKDAY = 2  # Wednesday close anchor; target remains constant until next Wednesday.


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


def _rank_scores(raw: Dict[str, float], floor: float = 0.0, cap: float = 2.0) -> Dict[str, float]:
    return {s: max(floor, min(cap, 1.0 + z)) for s, z in _zscore(raw).items()}


def _rebalance_slice(close: pd.DataFrame) -> pd.DataFrame:
    """Use last Wednesday-or-earlier observation to reduce daily target churn."""
    if close.empty:
        return close
    idx = close.index
    asof = idx[-1]
    candidates = idx[idx.weekday == REBALANCE_WEEKDAY]
    candidates = candidates[candidates <= asof]
    if len(candidates) == 0:
        return close.iloc[:1]
    anchor = candidates[-1]
    return close.loc[:anchor]


def _allocate(weights: Dict[str, float], scores: Dict[str, float], budget: float) -> None:
    if budget <= 0:
        return
    total = sum(max(0.0, v) for v in scores.values())
    if total <= 0:
        names = [s for s in scores if s in weights]
        if not names:
            return
        for s in names:
            weights[s] += budget / len(names)
        return
    for s, score in scores.items():
        if s in weights and score > 0:
            weights[s] += budget * score / total


def _regime(close: pd.DataFrame) -> tuple[float, float]:
    spy_vol_fast = _vol(close, "SPY", FAST_WINDOW) or _vol(close, "SPY", 63)
    ief_vol = _vol(close, "IEF", 126) or 0.06
    eq_dd = min(_drawdown(close, "SPY", 63), _drawdown(close, "QQQ", 63))
    vol_pressure = max(0.0, min(1.0, (spy_vol_fast - 1.10 * ief_vol) / 0.28))
    dd_pressure = max(0.0, min(1.0, abs(min(0.0, eq_dd)) / 0.13))
    stress = max(0.0, min(1.0, 0.50 * vol_pressure + 0.50 * dd_pressure))
    trend_pack = [_ret(close, s, 126) for s in ("SPY", "QQQ", "IWM", "TLT", "GLD") if s in close.columns]
    trend_beta_penalty = sum(1 for r in trend_pack if r > 0.03) / max(len(trend_pack), 1)
    return stress, trend_beta_penalty


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

    stress, trend_penalty = _regime(close)
    weights = {s: 0.0 for s in output_symbols}

    # More cash and less equity/commodity budget than AR-049; this is the
    # strengthened orthogonality brake against AR-015/AR-037 trend beta.
    equity_budget = 0.055 * (1.0 - 0.75 * stress) * (1.0 - 0.85 * trend_penalty)
    duration_budget = 0.34 + 0.12 * stress + 0.05 * trend_penalty
    haven_budget = 0.26 + 0.10 * stress
    carry_budget = 0.075 * (1.0 - 0.45 * stress) * (1.0 - 0.70 * trend_penalty)
    cash_budget = 0.22 + 0.12 * trend_penalty + 0.05 * stress
    risky_total = equity_budget + duration_budget + haven_budget + carry_budget
    if risky_total + cash_budget > 1.0:
        scale = (1.0 - cash_budget) / max(risky_total, 1e-12)
        equity_budget *= scale
        duration_budget *= scale
        haven_budget *= scale
        carry_budget *= scale

    eq_raw: Dict[str, float] = {}
    for s in EQUITIES:
        if s in available:
            carry_rank = sum(_ret(close, s, w) for w in LOOKBACKS) / len(LOOKBACKS)
            eq_raw[s] = -0.95 * _vol(close, s) + 0.35 * _drawdown(close, s, 126) - 0.45 * max(0.0, carry_rank)
    _allocate(weights, _rank_scores(eq_raw, cap=1.5), equity_budget)

    dur_raw: Dict[str, float] = {}
    for s in DURATION:
        if s in available:
            slow = 0.45 * _ret(close, s, 63) + 0.35 * _ret(close, s, 126) + 0.20 * _ret(close, s, 189)
            dur_raw[s] = slow - 0.80 * _vol(close, s)
    _allocate(weights, _rank_scores(dur_raw, cap=1.75), duration_budget)

    eq_fast = sum(_ret(close, s, 21) for s in EQUITIES if s in available) / max(sum(1 for s in EQUITIES if s in available), 1)
    haven_raw: Dict[str, float] = {}
    for s in HAVENS:
        if s in available:
            slow = 0.40 * _ret(close, s, 63) + 0.35 * _ret(close, s, 126) + 0.25 * _ret(close, s, 189)
            haven_raw[s] = slow - 0.30 * eq_fast - 0.65 * _vol(close, s)
    _allocate(weights, _rank_scores(haven_raw, cap=1.80), haven_budget)

    carry_raw: Dict[str, float] = {}
    for s in CARRY:
        if s in available:
            carry_mean = sum(_ret(close, s, w) for w in LOOKBACKS) / len(LOOKBACKS)
            churn_penalty = abs(_ret(close, s, 21))
            carry_raw[s] = 0.70 * carry_mean - 0.40 * churn_penalty - 0.70 * _vol(close, s)
    _allocate(weights, _rank_scores(carry_raw, cap=1.60), carry_budget)

    capped = {s: max(0.0, min(MAX_SINGLE_WEIGHT, _safe_float(weights.get(s, 0.0)))) for s in output_symbols}
    gross = sum(capped.values())
    if gross > 1.0:
        capped = {s: w / gross for s, w in capped.items()}
    return capped
