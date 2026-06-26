"""AR-059 ETF defensive momentum/carry rotation.

Long-only qfa model for SPY/QQQ/IWM/TLT/GLD/HYG/LQD/XLU. It blends slow
1-3 month momentum, trend stability, volatility/drawdown penalties, and a
stress-aware defensive preference. The implementation intentionally uses only
historical OHLCV bars supplied by qfa/Alpaca and returns target weights capped
at 35% gross per ETF with residual cash allowed.
"""
from __future__ import annotations

import math
from typing import Dict

import pandas as pd

UNIVERSE = ("SPY", "QQQ", "IWM", "TLT", "GLD", "HYG", "LQD", "XLU")
RISK_ASSETS = ("SPY", "QQQ", "IWM", "HYG")
DEFENSIVE_ASSETS = ("TLT", "GLD", "LQD", "XLU")

FAST_MOM = 63
SLOW_MOM = 126
VOL_WINDOW = 40
DD_WINDOW = 63
STABILITY_WINDOW = 84
MIN_HISTORY = 140
MAX_GROSS = 1.0
MAX_PER_ETF = 0.35
REBALANCE_WEEKDAY = 0  # Monday-only active rebalance; deterministic stale-weight proxy.


def _finite(x: float, default: float = 0.0) -> float:
    try:
        y = float(x)
    except Exception:
        return default
    return y if math.isfinite(y) else default


def _series(close: pd.DataFrame, symbol: str) -> pd.Series:
    if symbol not in close.columns:
        return pd.Series(dtype=float)
    return close[symbol].dropna()


def _ret(close: pd.DataFrame, symbol: str, window: int) -> float:
    s = _series(close, symbol)
    if len(s) <= window or s.iloc[-window - 1] <= 0:
        return 0.0
    return _finite(s.iloc[-1] / s.iloc[-window - 1] - 1.0)


def _vol(close: pd.DataFrame, symbol: str, window: int) -> float:
    s = _series(close, symbol)
    if len(s) <= window:
        return 0.30
    return max(0.02, _finite(s.pct_change().dropna().tail(window).std() * math.sqrt(252.0), 0.30))


def _drawdown(close: pd.DataFrame, symbol: str, window: int) -> float:
    s = _series(close, symbol).tail(window)
    if len(s) < 2:
        return 0.0
    return _finite((s.iloc[-1] / s.cummax().iloc[-1]) - 1.0)


def _trend_stability(close: pd.DataFrame, symbol: str, window: int) -> float:
    s = _series(close, symbol).tail(window + 1)
    if len(s) < window // 2:
        return 0.0
    r = s.pct_change().dropna()
    if r.empty:
        return 0.0
    positive_frac = float((r > 0).mean())
    downside = r[r < 0].std() if (r < 0).any() else 0.0
    return _finite(positive_frac - 0.5 - 4.0 * downside)


def _z(values: Dict[str, float]) -> Dict[str, float]:
    vals = [v for v in values.values() if math.isfinite(v)]
    if not vals:
        return {k: 0.0 for k in values}
    mean = sum(vals) / len(vals)
    sd = math.sqrt(sum((v - mean) ** 2 for v in vals) / max(1, len(vals) - 1))
    if sd <= 1e-12:
        return {k: 0.0 for k in values}
    return {k: max(-3.0, min(3.0, (v - mean) / sd)) for k, v in values.items()}


def _risk_stress(close: pd.DataFrame) -> float:
    spy_fast = _ret(close, "SPY", FAST_MOM)
    spy_dd = min(0.0, _drawdown(close, "SPY", DD_WINDOW))
    qqq_dd = min(0.0, _drawdown(close, "QQQ", DD_WINDOW))
    credit = _ret(close, "HYG", FAST_MOM) - _ret(close, "LQD", FAST_MOM)
    spy_vol = _vol(close, "SPY", VOL_WINDOW)
    vol_pressure = max(0.0, min(1.0, (spy_vol - 0.16) / 0.24))
    dd_pressure = max(0.0, min(1.0, abs(min(spy_dd, qqq_dd)) / 0.14))
    mom_pressure = 1.0 if spy_fast < 0 else 0.0
    credit_pressure = 1.0 if credit < -0.03 else 0.0
    return max(0.0, min(1.0, 0.35 * vol_pressure + 0.35 * dd_pressure + 0.20 * mom_pressure + 0.10 * credit_pressure))


def _target_weights(close: pd.DataFrame, output_symbols: list[str]) -> dict[str, float]:
    available = [s for s in output_symbols if s in UNIVERSE and s in close.columns]
    if len(close) < MIN_HISTORY or len(available) < 5:
        return {s: 0.0 for s in output_symbols}

    stress = _risk_stress(close)
    raw = {}
    for s in available:
        mom = 0.60 * _ret(close, s, FAST_MOM) + 0.40 * _ret(close, s, SLOW_MOM)
        vol = _vol(close, s, VOL_WINDOW)
        dd = _drawdown(close, s, DD_WINDOW)
        carry_proxy = mom / vol + 0.75 * _trend_stability(close, s, STABILITY_WINDOW)
        defensive_bonus = stress * (0.55 if s in DEFENSIVE_ASSETS else -0.55)
        credit_penalty = -0.20 * stress if s == "HYG" else 0.0
        raw[s] = carry_proxy + 1.2 * dd + defensive_bonus + credit_penalty

    scores = _z(raw)
    positive = {s: max(0.0, 1.0 + scores[s]) for s in available}

    # Reduce equity/credit budget during stress; residual remains cash.
    risk_budget_cap = 0.78 * (1.0 - stress) + 0.28 * stress
    defensive_budget_cap = 0.22 * (1.0 - stress) + 0.67 * stress
    weights = {s: 0.0 for s in output_symbols}
    for sleeve in (RISK_ASSETS, DEFENSIVE_ASSETS):
        names = [s for s in sleeve if s in positive]
        budget = risk_budget_cap if sleeve == RISK_ASSETS else defensive_budget_cap
        total = sum(positive[s] for s in names)
        if total > 0 and budget > 0:
            for s in names:
                weights[s] = budget * positive[s] / total

    capped = {s: min(MAX_PER_ETF, max(0.0, _finite(weights.get(s, 0.0)))) for s in output_symbols}
    gross = sum(capped.values())
    if gross > MAX_GROSS:
        capped = {s: w / gross for s, w in capped.items()}
    return capped


def generate_signals(context) -> dict[str, float]:
    output_symbols = list(context.symbols)
    if context.prices is None or context.prices.empty:
        return {s: 0.0 for s in output_symbols}
    prices = context.prices.copy()
    prices["timestamp"] = pd.to_datetime(prices["timestamp"], utc=True)
    close = prices.pivot(index="timestamp", columns="symbol", values="close").sort_index().ffill()
    # qfa calls this function daily and does not provide persistent previous
    # target weights. To implement a weekly stale-weight style signal without
    # mutable state, score only through the most recent Monday close; later
    # weekdays reuse that same deterministic snapshot until the next Monday.
    if not close.empty and close.index[-1].weekday() != REBALANCE_WEEKDAY:
        monday_dates = [idx for idx in close.index if idx.weekday() == REBALANCE_WEEKDAY]
        if monday_dates:
            close = close.loc[:monday_dates[-1]]
    return _target_weights(close, output_symbols)
