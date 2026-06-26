"""AR-049 orthogonality-constrained ETF carry/defensive allocation.

QFA contract: expose generate_signals(context) -> dict[str, float].

Refines AR-037 by explicitly suppressing equity/momentum beta that made AR-037
redundant with AR-015.  The model keeps the same liquid ETF/carry-defensive
family but allocates mostly to duration, gold, USD/JPY haven proxies and cash,
with only small low-volatility equity exposure.  It uses only OHLCV bars already
present in qfa's Alpaca-backed context and never places orders.
"""

from __future__ import annotations

import math
from typing import Dict

import pandas as pd

UNIVERSE = ("SPY", "QQQ", "IWM", "TLT", "IEF", "GLD", "USO", "FXE", "FXY", "UUP")
EQUITIES = ("SPY", "QQQ", "IWM")
DURATION = ("TLT", "IEF")
HAVENS = ("GLD", "UUP", "FXY")
ALT_CARRY = ("GLD", "USO", "FXE", "FXY", "UUP")

CARRY_WINDOW = 126
DEF_WINDOW = 63
VOL_WINDOW = 63
FAST_WINDOW = 21
MIN_HISTORY = 150
MAX_SINGLE_WEIGHT = 0.28
BASE_CASH = 0.08
MAX_EQUITY_BUDGET = 0.10
MAX_COMMODITY_BUDGET = 0.10


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


def _vol(close: pd.DataFrame, symbol: str, window: int) -> float:
    s = _series(close, symbol)
    if len(s) <= window:
        return 0.0
    returns = s.pct_change().dropna().tail(window)
    return _safe_float(returns.std() * math.sqrt(252.0))


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


def _regime(close: pd.DataFrame) -> tuple[float, float]:
    """Return stress level [0,1] and trend-correlation penalty [0,1]."""
    spy_vol = _vol(close, "SPY", FAST_WINDOW) or _vol(close, "SPY", VOL_WINDOW)
    ief_vol = _vol(close, "IEF", VOL_WINDOW) or 0.06
    spy_dd = _drawdown(close, "SPY", DEF_WINDOW)
    qqq_dd = _drawdown(close, "QQQ", DEF_WINDOW)
    equity_dd = min(spy_dd, qqq_dd)
    vol_pressure = max(0.0, min(1.0, (spy_vol - 1.15 * ief_vol) / 0.30))
    dd_pressure = max(0.0, min(1.0, abs(min(0.0, equity_dd)) / 0.14))
    stress = max(0.0, min(1.0, 0.55 * vol_pressure + 0.45 * dd_pressure))

    # If broad equity/duration/commodity momentum are all positive, AR-015-style
    # trend beta is likely high; hold more cash and duration instead of chasing.
    trend_pack = [_ret(close, s, CARRY_WINDOW) for s in ("SPY", "QQQ", "TLT", "GLD") if s in close.columns]
    positive_trend = sum(1 for r in trend_pack if r > 0.04) / max(len(trend_pack), 1)
    trend_penalty = max(0.0, min(1.0, positive_trend))
    return stress, trend_penalty


def _allocate(weights: dict[str, float], scores: Dict[str, float], budget: float) -> None:
    if budget <= 0:
        return
    total = sum(max(0.0, v) for v in scores.values())
    if total <= 0:
        equal = [s for s in scores if s in weights]
        if not equal:
            return
        for s in equal:
            weights[s] += budget / len(equal)
        return
    for sym, score in scores.items():
        if sym in weights and score > 0:
            weights[sym] += budget * score / total


def generate_signals(context) -> dict[str, float]:
    output_symbols = list(context.symbols)
    if context.prices is None or context.prices.empty:
        return {s: 0.0 for s in output_symbols}

    prices = context.prices.copy()
    prices["timestamp"] = pd.to_datetime(prices["timestamp"], utc=True)
    close = prices.pivot(index="timestamp", columns="symbol", values="close").sort_index().ffill()
    if len(close) < MIN_HISTORY:
        return {s: 0.0 for s in output_symbols}

    available = [s for s in output_symbols if s in UNIVERSE and s in close.columns]
    if len(available) < 5:
        return {s: 0.0 for s in output_symbols}

    stress, trend_penalty = _regime(close)
    weights = {s: 0.0 for s in output_symbols}

    # Explicit orthogonality constraint: keep equity sleeve small and reduce it
    # further when trend beta is likely elevated. The residual stays in cash.
    equity_budget = MAX_EQUITY_BUDGET * (1.0 - 0.70 * stress) * (1.0 - 0.75 * trend_penalty)
    duration_budget = 0.30 + 0.16 * stress + 0.04 * trend_penalty
    haven_budget = 0.28 + 0.10 * stress
    alt_budget = MAX_COMMODITY_BUDGET * (1.0 - 0.50 * stress) * (1.0 - 0.65 * trend_penalty)
    cash_budget = 0.16 + 0.10 * trend_penalty + 0.06 * stress
    total_budget = equity_budget + duration_budget + haven_budget + alt_budget + cash_budget
    if total_budget > 1.0:
        scale = (1.0 - cash_budget) / max(equity_budget + duration_budget + haven_budget + alt_budget, 1e-12)
        equity_budget *= scale
        duration_budget *= scale
        haven_budget *= scale
        alt_budget *= scale

    equity_raw = {}
    for s in EQUITIES:
        if s in available:
            # Prefer low-vol/shallow-drawdown equity, not high momentum.
            equity_raw[s] = -0.85 * _vol(close, s, VOL_WINDOW) + 0.25 * _drawdown(close, s, DEF_WINDOW) - 0.35 * max(0.0, _ret(close, s, CARRY_WINDOW))
    equity_scores = {s: max(0.0, 1.0 + z) for s, z in _zscore(equity_raw).items()}

    duration_raw = {}
    for s in DURATION:
        if s in available:
            # Carry proxy for bond ETFs: prefer stable positive intermediate trend
            # and low volatility; stress raises budget externally.
            duration_raw[s] = 0.55 * _ret(close, s, DEF_WINDOW) + 0.25 * _ret(close, s, CARRY_WINDOW) - 0.70 * _vol(close, s, VOL_WINDOW)
    duration_scores = {s: max(0.0, 1.0 + z) for s, z in _zscore(duration_raw).items()}

    haven_raw = {}
    eq_fast = sum(_ret(close, s, FAST_WINDOW) for s in EQUITIES if s in available) / max(sum(1 for s in EQUITIES if s in available), 1)
    for s in HAVENS:
        if s in available:
            haven_raw[s] = 0.45 * (_ret(close, s, DEF_WINDOW) - 0.25 * eq_fast) - 0.45 * _vol(close, s, VOL_WINDOW)
    haven_scores = {s: max(0.0, 1.0 + z) for s, z in _zscore(haven_raw).items()}

    alt_raw = {}
    for s in ALT_CARRY:
        if s in available:
            # Cross-sectional carry proxy after suppressing strong trend followers.
            trend = _ret(close, s, CARRY_WINDOW)
            alt_raw[s] = 0.55 * trend - 0.45 * abs(_ret(close, s, FAST_WINDOW)) - 0.55 * _vol(close, s, VOL_WINDOW)
    alt_scores = {s: max(0.0, min(1.75, 1.0 + z)) for s, z in _zscore(alt_raw).items()}

    _allocate(weights, equity_scores, equity_budget)
    _allocate(weights, duration_scores, duration_budget)
    _allocate(weights, haven_scores, haven_budget)
    _allocate(weights, alt_scores, alt_budget)

    capped = {s: max(0.0, min(MAX_SINGLE_WEIGHT, _safe_float(weights.get(s, 0.0)))) for s in output_symbols}
    gross = sum(capped.values())
    if gross > 1.0:
        capped = {s: w / gross for s, w in capped.items()}
    return capped
