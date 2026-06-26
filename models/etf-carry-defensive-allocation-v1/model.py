"""AR-037 liquid ETF carry/defensive allocation proxy.

This qfa model uses only Alpaca OHLCV bars available to the backtester. It is
intended to be mechanistically distinct from pure price time-series momentum:
weights are built from slow cross-asset carry/defensive proxies, volatility risk
budgeting, and regime-sensitive sleeve caps rather than following each asset's
own trend in isolation.
"""

from __future__ import annotations

import math
from typing import Dict

import pandas as pd

UNIVERSE = ("SPY", "QQQ", "IWM", "TLT", "IEF", "GLD", "USO", "FXE", "FXY", "UUP")
EQUITIES = ("SPY", "QQQ", "IWM")
DEFENSIVE = ("TLT", "IEF", "GLD", "UUP", "FXY")
COMMODITY_FX = ("GLD", "USO", "FXE", "FXY", "UUP")

CARRY_WINDOW = 126
DEFENSIVE_WINDOW = 60
VOL_WINDOW = 60
SHORT_VOL_WINDOW = 20
MIN_HISTORY = 150
EQUITY_CAP_RISK_ON = 0.50
EQUITY_CAP_RISK_OFF = 0.25
MAX_SINGLE_WEIGHT = 0.30
CASH_FLOOR_RISK_OFF = 0.10


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
    """Return risk_aversion [0,1] and equity cap.

    Risk aversion rises when broad equity drawdown and volatility are elevated
    relative to intermediate Treasuries. This is a defensive/carry gate, not a
    long/short trend signal for each ETF.
    """
    spy_vol = _vol(close, "SPY", SHORT_VOL_WINDOW) or _vol(close, "SPY", VOL_WINDOW)
    ief_vol = _vol(close, "IEF", VOL_WINDOW) or 0.06
    spy_dd = _drawdown(close, "SPY", DEFENSIVE_WINDOW)
    qqq_dd = _drawdown(close, "QQQ", DEFENSIVE_WINDOW)
    equity_dd = min(spy_dd, qqq_dd)
    vol_pressure = max(0.0, min(1.0, (spy_vol - 1.25 * ief_vol) / 0.35))
    dd_pressure = max(0.0, min(1.0, abs(min(0.0, equity_dd)) / 0.16))
    risk_aversion = max(0.0, min(1.0, 0.55 * vol_pressure + 0.45 * dd_pressure))
    equity_cap = EQUITY_CAP_RISK_ON * (1.0 - risk_aversion) + EQUITY_CAP_RISK_OFF * risk_aversion
    return risk_aversion, equity_cap


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

    risk_aversion, equity_cap = _regime(close)

    # Equity sleeve: favor broad/quality equity exposure only when equity carry
    # proxy (short realized volatility and shallow drawdown) is attractive.
    equity_raw = {}
    for s in EQUITIES:
        if s not in available:
            continue
        carry_proxy = -0.70 * _vol(close, s, VOL_WINDOW) + 0.30 * _drawdown(close, s, DEFENSIVE_WINDOW)
        equity_raw[s] = carry_proxy
    equity_scores = _zscore(equity_raw)
    equity_pos = {s: max(0.0, 1.0 + score) for s, score in equity_scores.items()}

    # Defensive/carry sleeve: prefer duration/gold/dollar-yen havens when they
    # have delivered low-vol positive relative carry versus equities.
    defensive_raw = {}
    equity_basket_ret = sum(_ret(close, s, DEFENSIVE_WINDOW) for s in EQUITIES if s in available) / max(
        sum(1 for s in EQUITIES if s in available), 1
    )
    for s in DEFENSIVE:
        if s not in available:
            continue
        relative_carry = _ret(close, s, DEFENSIVE_WINDOW) - 0.35 * equity_basket_ret
        stability = -0.60 * _vol(close, s, VOL_WINDOW)
        defensive_raw[s] = relative_carry + stability
    defensive_scores = _zscore(defensive_raw)
    defensive_pos = {s: max(0.0, 1.0 + score) for s, score in defensive_scores.items()}

    # Commodity/currency carry approximation: cross-sectional relative carry
    # among GLD/USO/FX baskets, volatility penalized, capped to avoid becoming a
    # simple trend follower.
    carry_raw = {}
    for s in COMMODITY_FX:
        if s not in available:
            continue
        carry_raw[s] = _ret(close, s, CARRY_WINDOW) - 0.50 * _vol(close, s, VOL_WINDOW)
    carry_scores = _zscore(carry_raw)
    carry_pos = {s: max(0.0, min(2.0, 1.0 + score)) for s, score in carry_scores.items()}

    weights = {s: 0.0 for s in output_symbols}
    eq_budget = equity_cap * (1.0 - 0.35 * risk_aversion)
    def_budget = 0.35 + 0.35 * risk_aversion
    carry_budget = max(0.0, 1.0 - eq_budget - def_budget - CASH_FLOOR_RISK_OFF * risk_aversion)

    def _allocate(scores: Dict[str, float], budget: float) -> None:
        total = sum(v for v in scores.values() if v > 0)
        if total <= 0 or budget <= 0:
            return
        for sym, score in scores.items():
            if sym in weights and score > 0:
                weights[sym] += budget * score / total

    _allocate(equity_pos, eq_budget)
    _allocate(defensive_pos, def_budget)
    _allocate(carry_pos, carry_budget)

    # Cap concentration and leave residual in cash; qfa normalizes only if gross
    # exceeds one, so long-only weights below one are preserved as defensive cash.
    capped = {s: max(0.0, min(MAX_SINGLE_WEIGHT, _safe_float(weights.get(s, 0.0)))) for s in output_symbols}
    gross = sum(capped.values())
    if gross > 1.0:
        capped = {s: w / gross for s, w in capped.items()}
    return capped
