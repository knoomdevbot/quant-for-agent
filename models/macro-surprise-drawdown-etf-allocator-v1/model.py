"""AR-063 macro-surprise drawdown-state ETF allocator for qfa.

Rule-based, long-only ETF allocator using only historical OHLCV bars supplied in
qfa AlphaContext. It is intentionally distinct from AR-051's slow cross-sectional
momentum/correlation defensive rotation: it keys off market drawdown state,
realized-volatility shocks, credit/duration/gold/defensive-equity proxy shocks,
and a simple recovery half-life proxy.
"""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

UNIVERSE = ["SPY", "QQQ", "TLT", "IEF", "GLD", "XLU", "XLP", "XLV", "HYG", "LQD", "SHY"]
EQUITY = ["SPY", "QQQ"]
DEFENSIVE_EQ = ["XLU", "XLP", "XLV"]
DURATION = ["TLT", "IEF"]
CREDIT = ["HYG", "LQD"]


def _pivot(prices: pd.DataFrame, field: str = "close") -> pd.DataFrame:
    px = prices.copy()
    px["timestamp"] = pd.to_datetime(px["timestamp"], utc=True)
    return px.pivot(index="timestamp", columns="symbol", values=field).sort_index().ffill()


def _safe_last(s: pd.Series, default: float = 0.0) -> float:
    s = pd.to_numeric(s, errors="coerce").dropna()
    if s.empty:
        return default
    return float(s.iloc[-1])


def _ret(close: pd.DataFrame, symbol: str, n: int) -> float:
    if symbol not in close or len(close[symbol].dropna()) <= n:
        return 0.0
    s = close[symbol].dropna()
    return float(s.iloc[-1] / s.iloc[-1 - n] - 1.0)


def _z(series: pd.Series, window: int = 63) -> float:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if len(s) < max(20, window // 2):
        return 0.0
    sample = s.iloc[-window:]
    sd = float(sample.std(ddof=1))
    if not math.isfinite(sd) or sd <= 0:
        return 0.0
    return float((sample.iloc[-1] - sample.mean()) / sd)


def _drawdown(close: pd.DataFrame, symbol: str = "SPY", lookback: int = 126) -> float:
    if symbol not in close:
        return 0.0
    s = close[symbol].dropna().iloc[-lookback:]
    if len(s) < 20:
        return 0.0
    peak = float(s.max())
    return float(s.iloc[-1] / peak - 1.0) if peak > 0 else 0.0


def _vol_z(close: pd.DataFrame, symbol: str = "SPY", lookback: int = 63) -> float:
    if symbol not in close:
        return 0.0
    rets = close[symbol].pct_change()
    rv = rets.rolling(10).std() * math.sqrt(252)
    return _z(rv, lookback)


def _normalize(weights: dict[str, float]) -> dict[str, float]:
    clean = {s: max(0.0, float(weights.get(s, 0.0))) for s in UNIVERSE}
    gross = sum(clean.values())
    if gross <= 0:
        return {s: (1.0 if s == "SHY" else 0.0) for s in UNIVERSE}
    # Soft concentration cap, then renormalize. qfa will normalize again.
    capped = {s: min(v / gross, 0.35) for s, v in clean.items()}
    gross2 = sum(capped.values())
    return {s: (v / gross2 if gross2 else 0.0) for s, v in capped.items()}


def generate_signals(context: Any) -> dict[str, float]:
    """Return target weights by symbol for qfa backtests/trading harnesses."""
    prices = getattr(context, "prices", None)
    symbols = list(getattr(context, "symbols", UNIVERSE))
    if prices is None or len(prices) < 80:
        return {s: 0.0 for s in symbols}

    close = _pivot(prices, "close")
    if "SPY" not in close or len(close.dropna(how="all")) < 80:
        return {s: 0.0 for s in symbols}

    dd126 = _drawdown(close, "SPY", 126)
    dd252 = _drawdown(close, "SPY", 252)
    volshock = _vol_z(close, "SPY", 63)

    spy20 = _ret(close, "SPY", 20)
    spy5 = _ret(close, "SPY", 5)
    credit5 = _ret(close, "HYG", 5) - _ret(close, "LQD", 5)
    gold5 = _ret(close, "GLD", 5) - _ret(close, "SPY", 5)
    def5 = sum(_ret(close, s, 5) for s in DEFENSIVE_EQ) / 3.0 - _ret(close, "SPY", 5)

    # Proxy surprise: recent shocks relative to their trailing behavior.
    rets5 = close.pct_change(5)
    credit_series = rets5.get("HYG", pd.Series(dtype=float)) - rets5.get("LQD", pd.Series(dtype=float))
    dur_series = rets5.get("TLT", pd.Series(dtype=float)) - rets5.get("IEF", pd.Series(dtype=float))
    gold_series = rets5.get("GLD", pd.Series(dtype=float)) - rets5.get("SPY", pd.Series(dtype=float))
    def_series = sum(rets5.get(s, pd.Series(dtype=float)) for s in DEFENSIVE_EQ) / 3.0 - rets5.get("SPY", pd.Series(dtype=float))
    credit_z = _z(credit_series, 63)
    duration_z = _z(dur_series, 63)
    gold_z = _z(gold_series, 63)
    defensive_z = _z(def_series, 63)

    stress_score = 0.0
    stress_score += max(0.0, (-dd126 - 0.06) / 0.12)
    stress_score += max(0.0, (-dd252 - 0.10) / 0.18)
    stress_score += max(0.0, volshock / 2.0)
    stress_score += max(0.0, -credit_z / 2.0)
    stress_score += max(0.0, defensive_z / 3.0)
    stress_score = min(2.0, stress_score)

    recovering = (dd126 < -0.04 and spy20 > 0.025 and spy5 > -0.015 and credit_z > -0.25)
    severe_stress = stress_score >= 1.0 or (dd126 < -0.12 and volshock > 0.25)

    w: dict[str, float]
    if severe_stress and not recovering:
        w = {"TLT": 0.24, "IEF": 0.18, "GLD": 0.20, "XLU": 0.11, "XLP": 0.11, "XLV": 0.08, "SHY": 0.08}
        if duration_z < -1.0:  # rates rising against long duration; prefer shorter duration/cash.
            w["TLT"] -= 0.10
            w["IEF"] += 0.05
            w["SHY"] += 0.05
        if gold_z > 1.0:
            w["GLD"] += 0.05
            w["SHY"] -= 0.05
    elif recovering:
        # Drawdown recovery half-life proxy: risk back in when rebound is broad and credit stabilizes.
        w = {"SPY": 0.30, "QQQ": 0.18, "HYG": 0.17, "LQD": 0.10, "GLD": 0.10, "IEF": 0.10, "SHY": 0.05}
        if credit5 > 0.01:
            w["HYG"] += 0.05
            w["SHY"] -= 0.05
    elif stress_score > 0.35:
        w = {"SPY": 0.12, "QQQ": 0.06, "TLT": 0.18, "IEF": 0.16, "GLD": 0.16, "XLU": 0.11, "XLP": 0.10, "XLV": 0.08, "SHY": 0.03}
    else:
        # Benign state: modest macro-surprise tilt, not pure momentum rank.
        w = {"SPY": 0.28, "QQQ": 0.18, "HYG": 0.14, "LQD": 0.10, "GLD": 0.08, "IEF": 0.08, "XLU": 0.05, "XLP": 0.04, "XLV": 0.03, "SHY": 0.02}
        if credit_z < -0.75 or credit5 < -0.01:
            w["HYG"] -= 0.07
            w["LQD"] += 0.03
            w["SHY"] += 0.04
        if duration_z > 0.75 and volshock > -0.5:
            w["TLT"] = w.get("TLT", 0.0) + 0.05
            w["SPY"] -= 0.03
            w["QQQ"] -= 0.02
        if gold_z > 1.0 or gold5 > 0.02:
            w["GLD"] += 0.04
            w["SPY"] -= 0.02
            w["HYG"] -= 0.02
        if def5 > 0.01:
            w["XLU"] += 0.02
            w["XLP"] += 0.02
            w["SPY"] -= 0.04

    normalized = _normalize(w)
    return {s: float(normalized.get(s, 0.0)) for s in symbols}
