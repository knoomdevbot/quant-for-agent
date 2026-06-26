"""AR-072 beta/redundancy-constrained macro drawdown allocator for qfa.

Rule-based long-only ETF allocator using only historical OHLCV bars supplied by
qfa/Alpaca.  It refines AR-063 by explicitly capping estimated SPY beta,
reducing overlap with common ETF risk-off/carry sleeves, and using slow 10-day
change gates to limit turnover.
"""
from __future__ import annotations

import math
from typing import Any

import pandas as pd

UNIVERSE = ["SPY", "QQQ", "TLT", "IEF", "GLD", "XLU", "XLP", "XLV", "HYG", "LQD", "SHY"]
DEFENSIVE_EQ = ["XLU", "XLP", "XLV"]
BETA_CAP = 0.30
SHOCK_WINDOW = 126
TURNOVER_BRAKE_DAYS = 10


def _pivot(prices: pd.DataFrame, field: str = "close") -> pd.DataFrame:
    px = prices.copy()
    px["timestamp"] = pd.to_datetime(px["timestamp"], utc=True)
    return px.pivot(index="timestamp", columns="symbol", values=field).sort_index().ffill()


def _ret(close: pd.DataFrame, symbol: str, n: int) -> float:
    if symbol not in close:
        return 0.0
    s = close[symbol].dropna()
    if len(s) <= n:
        return 0.0
    return float(s.iloc[-1] / s.iloc[-1 - n] - 1.0)


def _z(series: pd.Series, window: int = SHOCK_WINDOW) -> float:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if len(s) < max(30, window // 2):
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


def _vol_z(close: pd.DataFrame, symbol: str = "SPY", lookback: int = SHOCK_WINDOW) -> float:
    if symbol not in close:
        return 0.0
    rv = close[symbol].pct_change().rolling(10).std() * math.sqrt(252)
    return _z(rv, lookback)


def _rolling_betas(close: pd.DataFrame, window: int = 126) -> dict[str, float]:
    if "SPY" not in close:
        return {s: 0.0 for s in UNIVERSE}
    rets = close.pct_change().dropna(how="all").iloc[-window:]
    mkt = pd.to_numeric(rets.get("SPY", pd.Series(dtype=float)), errors="coerce")
    var = float(mkt.var(ddof=1)) if len(mkt.dropna()) > 20 else 0.0
    out: dict[str, float] = {}
    for s in UNIVERSE:
        r = pd.to_numeric(rets.get(s, pd.Series(dtype=float)), errors="coerce")
        aligned = pd.concat([r, mkt], axis=1).dropna()
        if var <= 0 or len(aligned) < 20:
            out[s] = 1.0 if s in {"SPY", "QQQ", "HYG", "XLU", "XLP", "XLV"} else 0.0
        else:
            out[s] = float(aligned.iloc[:, 0].cov(aligned.iloc[:, 1]) / var)
    out["SPY"] = 1.0
    out["SHY"] = min(out.get("SHY", 0.0), 0.05)
    return out


def _normalize(weights: dict[str, float]) -> dict[str, float]:
    clean = {s: max(0.0, float(weights.get(s, 0.0))) for s in UNIVERSE}
    gross = sum(clean.values())
    if gross <= 0:
        return {s: (1.0 if s == "SHY" else 0.0) for s in UNIVERSE}
    capped = {s: min(v / gross, 0.32) for s, v in clean.items()}
    gross2 = sum(capped.values())
    return {s: (v / gross2 if gross2 else 0.0) for s, v in capped.items()}


def _cap_portfolio_beta(w: dict[str, float], betas: dict[str, float], cap: float = BETA_CAP) -> dict[str, float]:
    w = _normalize(w)
    beta = sum(w.get(s, 0.0) * betas.get(s, 0.0) for s in UNIVERSE)
    if beta <= cap:
        return w
    high_beta = [s for s in ["QQQ", "SPY", "HYG", "XLU", "XLV", "XLP"] if w.get(s, 0.0) > 0]
    for s in sorted(high_beta, key=lambda x: betas.get(x, 0.0), reverse=True):
        if beta <= cap:
            break
        removable = min(w[s], (beta - cap) / max(0.05, betas.get(s, 1.0) - betas.get("SHY", 0.0)))
        removable = max(0.0, min(removable, w[s]))
        w[s] -= removable
        # split replacement between SHY and IEF to reduce pure cash drag but keep beta low
        w["SHY"] = w.get("SHY", 0.0) + 0.70 * removable
        w["IEF"] = w.get("IEF", 0.0) + 0.30 * removable
        beta = sum(w.get(k, 0.0) * betas.get(k, 0.0) for k in UNIVERSE)
    return _normalize(w)


def _rebalance_gate(asof: Any) -> bool:
    try:
        ts = pd.Timestamp(asof)
        # deterministic slow gate: only allow materially different allocations every ~10 sessions.
        return (int(ts.dayofyear) % TURNOVER_BRAKE_DAYS) in (0, 1)
    except Exception:
        return True


def generate_signals(context: Any) -> dict[str, float]:
    """Return target weights by symbol for qfa backtests/trading harnesses."""
    prices = getattr(context, "prices", None)
    symbols = list(getattr(context, "symbols", UNIVERSE))
    if prices is None or len(prices) < 90:
        return {s: 0.0 for s in symbols}

    close = _pivot(prices, "close")
    if "SPY" not in close or len(close.dropna(how="all")) < 90:
        return {s: 0.0 for s in symbols}

    asof = getattr(context, "as_of", close.index[-1])
    dd126 = _drawdown(close, "SPY", 126)
    dd252 = _drawdown(close, "SPY", 252)
    volshock = _vol_z(close, "SPY", SHOCK_WINDOW)
    spy20 = _ret(close, "SPY", 20)
    spy5 = _ret(close, "SPY", 5)
    credit5 = _ret(close, "HYG", 5) - _ret(close, "LQD", 5)

    rets5 = close.pct_change(5)
    credit_series = rets5.get("HYG", pd.Series(dtype=float)) - rets5.get("LQD", pd.Series(dtype=float))
    dur_series = rets5.get("TLT", pd.Series(dtype=float)) - rets5.get("IEF", pd.Series(dtype=float))
    gold_series = rets5.get("GLD", pd.Series(dtype=float)) - rets5.get("SPY", pd.Series(dtype=float))
    def_series = sum(rets5.get(s, pd.Series(dtype=float)) for s in DEFENSIVE_EQ) / 3.0 - rets5.get("SPY", pd.Series(dtype=float))
    credit_z = _z(credit_series, SHOCK_WINDOW)
    duration_z = _z(dur_series, SHOCK_WINDOW)
    gold_z = _z(gold_series, SHOCK_WINDOW)
    defensive_z = _z(def_series, SHOCK_WINDOW)

    stress_score = 0.0
    stress_score += max(0.0, (-dd126 - 0.07) / 0.13)
    stress_score += max(0.0, (-dd252 - 0.12) / 0.20)
    stress_score += max(0.0, volshock / 2.5)
    stress_score += max(0.0, -credit_z / 2.5)
    stress_score = min(2.0, stress_score)

    recovering = dd126 < -0.05 and spy20 > 0.03 and spy5 > -0.012 and credit_z > -0.35
    severe_stress = stress_score >= 1.05 or (dd126 < -0.14 and volshock > 0.35)
    slow_gate = _rebalance_gate(asof)

    if severe_stress and not recovering:
        # Redundancy penalty: avoid the AR-037/AR-043 heavy TLT+GLD+XLU stack; emphasize IEF/SHY/LQD.
        w = {"IEF": 0.27, "LQD": 0.18, "GLD": 0.14, "XLV": 0.11, "XLP": 0.08, "TLT": 0.07, "SHY": 0.15}
        if duration_z < -0.7:
            w["TLT"] -= 0.05
            w["SHY"] += 0.05
        if gold_z > 1.25:
            w["GLD"] += 0.03
            w["LQD"] -= 0.03
    elif recovering:
        w = {"SPY": 0.14, "QQQ": 0.07, "HYG": 0.12, "LQD": 0.21, "IEF": 0.17, "GLD": 0.09, "XLV": 0.08, "SHY": 0.12}
        if credit5 > 0.012 and slow_gate:
            w["HYG"] += 0.04
            w["SHY"] -= 0.04
    elif stress_score > 0.35:
        w = {"SPY": 0.08, "QQQ": 0.03, "IEF": 0.23, "LQD": 0.20, "GLD": 0.12, "XLV": 0.10, "XLP": 0.06, "SHY": 0.18}
    else:
        # Benign state: beta-capped carry/core mix, not pure risk-on.
        w = {"SPY": 0.15, "QQQ": 0.06, "HYG": 0.11, "LQD": 0.22, "IEF": 0.18, "GLD": 0.08, "XLV": 0.06, "XLP": 0.04, "SHY": 0.10}
        if slow_gate and (credit_z < -0.70 or credit5 < -0.012):
            w["HYG"] -= 0.06
            w["LQD"] += 0.03
            w["SHY"] += 0.03
        if slow_gate and duration_z > 0.90 and volshock > -0.50:
            w["IEF"] += 0.04
            w["SPY"] -= 0.02
            w["QQQ"] -= 0.02
        if slow_gate and (gold_z > 1.20):
            w["GLD"] += 0.03
            w["HYG"] -= 0.03
        if slow_gate and defensive_z > 1.00:
            w["XLV"] += 0.03
            w["SPY"] -= 0.03

    constrained = _cap_portfolio_beta(w, _rolling_betas(close, 126), BETA_CAP)
    return {s: float(constrained.get(s, 0.0)) for s in symbols}
