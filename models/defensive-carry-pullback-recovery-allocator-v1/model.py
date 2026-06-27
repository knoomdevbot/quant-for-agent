"""AR-118 defensive-carry pullback-recovery ETF allocator.

QFA contract: expose generate_signals(context) -> dict[str, float]. Uses only
historical daily OHLCV bars supplied in context.prices; no external state/files.
"""
from __future__ import annotations

import math
from typing import Any

import pandas as pd

UNIVERSE = (
    "SHY", "IEF", "TLT", "GOVT", "TIP", "LQD", "HYG", "GLD", "SLV", "DBC", "USO", "DBA",
    "SPY", "QQQ", "IWM", "DIA", "USMV", "QUAL", "SPLV", "XLU", "XLP", "XLV", "XLE", "XLF",
    "XLI", "XLB", "XLRE", "XLC",
)
DEFENSIVE_CARRY = ("SHY", "IEF", "TLT", "GOVT", "TIP", "LQD", "HYG", "GLD", "USMV", "SPLV", "XLU", "XLP", "XLV")
RISK_CONTEXT = ("SPY", "HYG", "LQD")
MIN_HISTORY = 90
TREND_WINDOW = 63
PULLBACK_WINDOW = 5
VOL_WINDOW = 42
TOP_N = 3
MAX_GROSS = 0.95


def _safe(x: Any, default: float = 0.0) -> float:
    try:
        y = float(x)
    except Exception:
        return default
    return y if math.isfinite(y) else default


def _clip(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _prep(prices: pd.DataFrame) -> pd.DataFrame:
    data = prices.copy()
    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True)
    data = data[data["symbol"].isin(set(UNIVERSE) | set(RISK_CONTEXT))].sort_values(["timestamp", "symbol"])
    return data.pivot(index="timestamp", columns="symbol", values="close").sort_index().ffill()


def _ret(close: pd.DataFrame, symbol: str, window: int) -> float:
    if symbol not in close.columns:
        return 0.0
    s = close[symbol].dropna()
    if len(s) <= window or _safe(s.iloc[-window - 1]) <= 0:
        return 0.0
    return _safe(s.iloc[-1] / s.iloc[-window - 1] - 1.0)


def _vol(close: pd.DataFrame, symbol: str, window: int = VOL_WINDOW) -> float:
    if symbol not in close.columns:
        return 0.0
    r = close[symbol].dropna().pct_change().dropna().tail(window)
    if len(r) < 20:
        return 0.0
    return _safe(r.std(ddof=1) * math.sqrt(252.0))


def _stress_gate(close: pd.DataFrame) -> bool:
    # Predeclared benign/moderate stress only: soft equity pressure, no credit crash.
    spy20 = _ret(close, "SPY", 20)
    spy_vol = _vol(close, "SPY", 20)
    hyg20 = _ret(close, "HYG", 20)
    lqd20 = _ret(close, "LQD", 20)
    if spy20 < -0.08 or spy20 > 0.03:
        return False
    if spy_vol > 0.33:
        return False
    if hyg20 < -0.06 or lqd20 < -0.05:
        return False
    return True


def _score(close: pd.DataFrame, symbol: str) -> float:
    s = close[symbol].dropna() if symbol in close.columns else pd.Series(dtype=float)
    if len(s) < MIN_HISTORY:
        return -999.0
    trend = _ret(close, symbol, TREND_WINDOW)
    vol = max(_vol(close, symbol), 0.035)
    trend_rv = trend / vol
    if trend <= 0.0 or trend_rv <= 0.05:
        return -999.0
    ret5 = _ret(close, symbol, PULLBACK_WINDOW)
    daily = s.pct_change().dropna()
    hist5 = s.pct_change(PULLBACK_WINDOW).dropna().tail(84)
    sd5 = _safe(hist5.std(ddof=1), 0.0)
    pullback_z = _clip((-ret5) / sd5, 0.0, 3.0) if sd5 > 1e-9 else 0.0
    rebound = max(0.0, _safe(daily.tail(2).sum())) / max(vol / math.sqrt(252.0) * 2.0, 1e-6)
    carry_bias = 0.35 if symbol in DEFENSIVE_CARRY else -0.10
    low_vol_bonus = _clip((0.22 - vol) / 0.18, -0.5, 0.8)
    return 0.42 * _clip(trend_rv, 0.0, 2.0) + 0.30 * pullback_z + 0.18 * _clip(rebound, 0.0, 2.0) + carry_bias + 0.10 * low_vol_bonus


def generate_signals(context) -> dict[str, float]:
    symbols = list(context.symbols)
    if context.prices is None or context.prices.empty:
        return {s: 0.0 for s in symbols}
    close = _prep(context.prices)
    if len(close) < MIN_HISTORY or not _stress_gate(close):
        return {s: (MAX_GROSS if s == "SHY" and s in symbols else 0.0) for s in symbols}
    candidates = []
    for sym in UNIVERSE:
        if sym in symbols and sym in close.columns:
            sc = _score(close, sym)
            if sc > 0.35:
                candidates.append((sym, sc))
    candidates.sort(key=lambda x: x[1], reverse=True)
    picks = candidates[:TOP_N]
    weights = {s: 0.0 for s in symbols}
    if not picks:
        if "SHY" in symbols:
            weights["SHY"] = MAX_GROSS
        return weights
    total = sum(max(0.01, sc) for _, sc in picks)
    for sym, sc in picks:
        weights[sym] = MAX_GROSS * max(0.01, sc) / total
    return weights
