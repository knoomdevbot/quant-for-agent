"""AR-105 residualized two-sleeve macro stress/relief ETF allocator.

QFA contract: expose generate_signals(context) -> dict[str, float].
Research-only, long-only, gross <= 1 target weights using only OHLCV bars already
present in the qfa/Alpaca AlphaContext.  The model separates a defensive-stress
sleeve from a stress-abatement relief sleeve, then beta/correlation caps the
combined allocation by shifting excess beta toward SHY/IEF.
"""
from __future__ import annotations

import math
from typing import Any

import pandas as pd

UNIVERSE = [
    "SPY", "QQQ", "IWM", "DIA", "XLK", "XLI", "XLF", "XLV", "XLP", "XLU",
    "XLE", "XLB", "TLT", "IEF", "TIP", "LQD", "HYG", "SHY", "GLD", "SLV",
    "DBC", "USO", "VNQ", "MTUM", "QUAL", "USMV",
]
DEFENSIVE_STRESS = ["IEF", "TLT", "TIP", "LQD", "GLD", "XLU", "XLP", "XLV", "SHY", "USMV"]
RELIEF_REBOUND = ["SPY", "QQQ", "IWM", "DIA", "XLK", "XLI", "XLF", "HYG", "XLE", "XLB", "DBC", "QUAL", "MTUM"]
RISK_ASSETS = ["SPY", "QQQ", "IWM", "DIA", "XLK", "XLI", "XLF", "HYG", "XLE", "XLB", "DBC", "VNQ"]
BETA_CAP = 0.25
MAX_SINGLE_WEIGHT = 0.26
MIN_HISTORY = 180


def _pivot(prices: pd.DataFrame, field: str = "close") -> pd.DataFrame:
    px = prices.copy()
    px["timestamp"] = pd.to_datetime(px["timestamp"], utc=True)
    return px.pivot(index="timestamp", columns="symbol", values=field).sort_index().ffill()


def _ret(close: pd.DataFrame, symbol: str, n: int) -> float:
    if symbol not in close:
        return 0.0
    s = close[symbol].dropna()
    if len(s) <= n or s.iloc[-1 - n] <= 0:
        return 0.0
    out = float(s.iloc[-1] / s.iloc[-1 - n] - 1.0)
    return out if math.isfinite(out) else 0.0


def _z(series: pd.Series, window: int = 126) -> float:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if len(s) < max(40, window // 2):
        return 0.0
    sample = s.iloc[-window:]
    sd = float(sample.std(ddof=1))
    if not math.isfinite(sd) or sd <= 1e-12:
        return 0.0
    return float(max(-3.0, min(3.0, (sample.iloc[-1] - sample.mean()) / sd)))


def _drawdown(close: pd.DataFrame, symbol: str = "SPY", lookback: int = 126) -> float:
    if symbol not in close:
        return 0.0
    s = close[symbol].dropna().iloc[-lookback:]
    if len(s) < 40:
        return 0.0
    peak = float(s.max())
    return float(s.iloc[-1] / peak - 1.0) if peak > 0 else 0.0


def _realized_vol(close: pd.DataFrame, symbol: str, n: int = 20) -> float:
    if symbol not in close:
        return 0.0
    r = close[symbol].pct_change().dropna().tail(n)
    if len(r) < max(10, n // 2):
        return 0.0
    return float(r.std(ddof=1) * math.sqrt(252.0))


def _rolling_betas(close: pd.DataFrame, window: int = 126) -> dict[str, float]:
    rets = close.pct_change().dropna(how="all").iloc[-window:]
    mkt = pd.to_numeric(rets.get("SPY", pd.Series(dtype=float)), errors="coerce")
    var = float(mkt.var(ddof=1)) if len(mkt.dropna()) > 30 else 0.0
    out: dict[str, float] = {}
    defaults = {"SPY": 1.0, "QQQ": 1.15, "IWM": 1.2, "DIA": 0.9, "HYG": 0.45}
    for s in UNIVERSE:
        r = pd.to_numeric(rets.get(s, pd.Series(dtype=float)), errors="coerce")
        aligned = pd.concat([r, mkt], axis=1).dropna()
        if var <= 0 or len(aligned) < 30:
            out[s] = defaults.get(s, 0.15 if s in DEFENSIVE_STRESS else 0.8)
        else:
            out[s] = float(aligned.iloc[:, 0].cov(aligned.iloc[:, 1]) / var)
    out["SPY"] = 1.0
    out["SHY"] = min(out.get("SHY", 0.0), 0.05)
    return out


def _normalize(scores: dict[str, float], cap: float = MAX_SINGLE_WEIGHT) -> dict[str, float]:
    clean = {s: max(0.0, float(v)) for s, v in scores.items() if math.isfinite(float(v))}
    gross = sum(clean.values())
    if gross <= 0:
        return {}
    w = {s: min(v / gross, cap) for s, v in clean.items()}
    gross2 = sum(w.values())
    return {s: v / gross2 for s, v in w.items()} if gross2 > 0 else {}


def _breadth(close: pd.DataFrame, symbols: list[str], n: int = 20) -> float:
    vals = [_ret(close, s, n) > 0 for s in symbols if s in close]
    return float(sum(vals) / len(vals)) if vals else 0.0


def _state(close: pd.DataFrame) -> dict[str, float]:
    rets5 = close.pct_change(5)
    rets20 = close.pct_change(20)
    credit = rets5.get("HYG", pd.Series(dtype=float)) - rets5.get("LQD", pd.Series(dtype=float))
    duration = rets5.get("TLT", pd.Series(dtype=float)) - rets5.get("IEF", pd.Series(dtype=float))
    gold = rets5.get("GLD", pd.Series(dtype=float)) - rets5.get("SPY", pd.Series(dtype=float))
    commodities = rets20.get("DBC", pd.Series(dtype=float)) - rets20.get("SPY", pd.Series(dtype=float))
    defensives = (rets5.get("XLU", pd.Series(dtype=float)) + rets5.get("XLP", pd.Series(dtype=float)) + rets5.get("XLV", pd.Series(dtype=float))) / 3.0 - rets5.get("SPY", pd.Series(dtype=float))
    dd126 = _drawdown(close, "SPY", 126)
    dd252 = _drawdown(close, "SPY", 252)
    vol = close.get("SPY", pd.Series(dtype=float)).pct_change().rolling(10).std() * math.sqrt(252.0)
    vol_z = _z(vol, 126)
    credit_z = _z(credit, 126)
    duration_z = _z(duration, 126)
    gold_z = _z(gold, 126)
    commodity_z = _z(commodities, 126)
    defensive_z = _z(defensives, 126)
    breadth20 = _breadth(close, [s for s in RISK_ASSETS if s in close], 20)
    breadth5 = _breadth(close, [s for s in RISK_ASSETS if s in close], 5)
    stress = 0.0
    stress += max(0.0, (-dd126 - 0.055) / 0.13)
    stress += max(0.0, (-dd252 - 0.10) / 0.20)
    stress += max(0.0, vol_z / 2.35)
    stress += max(0.0, -credit_z / 2.25)
    stress += max(0.0, defensive_z / 2.75)
    stress += max(0.0, (0.42 - breadth20) / 0.42)
    stress = min(2.0, stress)
    abatement = 0.0
    abatement += max(0.0, (_ret(close, "SPY", 20) - 0.015) / 0.07)
    abatement += max(0.0, (breadth20 - 0.50) / 0.35)
    abatement += max(0.0, (breadth5 - 0.55) / 0.35)
    abatement += max(0.0, (credit_z + 0.40) / 1.80)
    abatement += max(0.0, -vol_z / 3.00)
    relief = min(1.0, abatement / 3.0) if (dd126 < -0.035 or stress > 0.35) else 0.0
    return {
        "stress": stress, "relief": relief, "dd126": dd126, "dd252": dd252, "vol_z": vol_z,
        "credit_z": credit_z, "duration_z": duration_z, "gold_z": gold_z,
        "commodity_z": commodity_z, "defensive_z": defensive_z, "breadth20": breadth20,
    }


def _stress_sleeve(close: pd.DataFrame, st: dict[str, float]) -> dict[str, float]:
    scores: dict[str, float] = {}
    for s in DEFENSIVE_STRESS:
        if s not in close:
            continue
        mom = 0.55 * _ret(close, s, 20) + 0.45 * _ret(close, s, 60)
        calm = -0.18 * _realized_vol(close, s, 20)
        score = 1.0 + 6.0 * mom + calm
        if s in {"IEF", "TIP", "LQD", "SHY"}:
            score += 0.25
        if s == "TLT" and st["duration_z"] < -0.75:
            score -= 0.65
        if s == "GLD":
            score += 0.25 * max(0.0, st["gold_z"])
        if s in {"XLU", "XLP", "XLV", "USMV"}:
            score += 0.15 * max(0.0, st["defensive_z"])
        scores[s] = score
    return _normalize(scores)


def _relief_sleeve(close: pd.DataFrame, st: dict[str, float]) -> dict[str, float]:
    scores: dict[str, float] = {}
    for s in RELIEF_REBOUND:
        if s not in close:
            continue
        r20 = _ret(close, s, 20)
        r5 = _ret(close, s, 5)
        rv = _realized_vol(close, s, 20)
        score = 0.80 + 5.0 * r20 + 2.0 * r5 - 0.22 * rv
        if s == "HYG":
            score += 0.35 * max(0.0, st["credit_z"] + 0.3)
        if s in {"XLE", "XLB", "DBC"}:
            score += 0.15 * max(0.0, st["commodity_z"])
        if s in {"QUAL", "MTUM"}:
            score += 0.12
        scores[s] = score
    return _normalize(scores, cap=0.22)


def _cap_beta(weights: dict[str, float], betas: dict[str, float], cap: float = BETA_CAP) -> dict[str, float]:
    w = dict(weights)
    beta = sum(w.get(s, 0.0) * betas.get(s, 0.0) for s in w)
    if beta <= cap:
        return w
    reducers = [s for s in w if w.get(s, 0.0) > 0 and betas.get(s, 0.0) > 0.25 and s not in {"SHY", "IEF"}]
    for s in sorted(reducers, key=lambda x: betas.get(x, 0.0), reverse=True):
        if beta <= cap:
            break
        replace_beta = 0.70 * betas.get("SHY", 0.0) + 0.30 * betas.get("IEF", 0.0)
        removable = min(w[s], (beta - cap) / max(0.05, betas.get(s, 1.0) - replace_beta))
        if removable <= 0:
            continue
        w[s] -= removable
        w["SHY"] = w.get("SHY", 0.0) + 0.70 * removable
        w["IEF"] = w.get("IEF", 0.0) + 0.30 * removable
        beta = sum(w.get(k, 0.0) * betas.get(k, 0.0) for k in w)
    return _normalize(w)


def compute_components(context: Any) -> dict[str, Any]:
    prices = getattr(context, "prices", None)
    symbols = list(getattr(context, "symbols", UNIVERSE))
    zero = {s: 0.0 for s in symbols}
    if prices is None or len(prices) < MIN_HISTORY:
        return {"combined": zero, "stress": zero, "relief": zero, "state": {}}
    close = _pivot(prices, "close")
    if "SPY" not in close or len(close.dropna(how="all")) < MIN_HISTORY:
        return {"combined": zero, "stress": zero, "relief": zero, "state": {}}
    st = _state(close)
    stress_raw = _stress_sleeve(close, st)
    relief_raw = _relief_sleeve(close, st)
    stress_budget = min(0.68, 0.18 + 0.30 * min(1.0, st["stress"]))
    relief_budget = min(0.38, 0.08 + 0.30 * st["relief"] * (1.0 - 0.25 * min(1.0, st["stress"])))
    cash_budget = max(0.12, 1.0 - stress_budget - relief_budget)
    combined: dict[str, float] = {s: 0.0 for s in symbols}
    stress_w = {s: 0.0 for s in symbols}
    relief_w = {s: 0.0 for s in symbols}
    for s, v in stress_raw.items():
        if s in combined:
            combined[s] += stress_budget * v
            stress_w[s] += stress_budget * v
    for s, v in relief_raw.items():
        if s in combined:
            combined[s] += relief_budget * v
            relief_w[s] += relief_budget * v
    if "SHY" in combined:
        combined["SHY"] += cash_budget
    elif "IEF" in combined:
        combined["IEF"] += cash_budget
    combined = _cap_beta(combined, _rolling_betas(close, 126), BETA_CAP)
    combined = {s: min(MAX_SINGLE_WEIGHT, max(0.0, float(combined.get(s, 0.0)))) for s in symbols}
    gross = sum(combined.values())
    if gross > 0:
        combined = {s: v / gross for s, v in combined.items()}
    return {"combined": combined, "stress": stress_w, "relief": relief_w, "state": st}


def generate_signals(context: Any) -> dict[str, float]:
    """Return target weights by symbol for qfa backtests/trading harnesses."""
    return compute_components(context)["combined"]
