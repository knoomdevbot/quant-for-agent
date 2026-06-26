"""AR-065 ETF realized-volatility term-state breadth allocator.

Research-only qfa alpha contract: generate_signals(context) -> dict[str, float].
Uses only historical OHLCV bars supplied by qfa/Alpaca. The signal is designed
as a divergent mechanism from AR-052: no VIXY sleeve and no TLT stress-carry
rule. It allocates among broad equity, defensive, commodity, sector, and cash
proxy ETFs from realized-volatility term-state breadth, downside-volatility
surprise, SPY drawdown state, and defensive momentum confirmation.
"""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

UNIVERSE = ["SPY", "QQQ", "IWM", "TLT", "GLD", "XLU", "XLE", "SHY"]
RISK_ON = ["SPY", "QQQ", "IWM", "XLE"]
DEFENSIVE = ["TLT", "GLD", "XLU", "SHY"]

PARAMS = {
    "vol_short": 10,
    "vol_medium": 20,
    "vol_slow": 60,
    "breadth_threshold": 0.60,
    "defensive_budget": 0.80,
    "drawdown_window": 126,
    "momentum_window": 60,
    "downside_window": 20,
    "turnover_brake_band": 0.06,
    "max_weight": 0.40,
}


def _pivot(prices: pd.DataFrame, field: str = "close") -> pd.DataFrame:
    px = prices.copy()
    px["timestamp"] = pd.to_datetime(px["timestamp"], utc=True)
    return px.pivot(index="timestamp", columns="symbol", values=field).sort_index().ffill()


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return default
    return out if math.isfinite(out) else default


def _realized_vol(rets: pd.DataFrame, window: int) -> pd.Series:
    if len(rets) < window + 1:
        return pd.Series(dtype=float)
    return rets.tail(window).std(ddof=1) * math.sqrt(252)


def _ret(close: pd.DataFrame, symbol: str, n: int) -> float:
    if symbol not in close:
        return 0.0
    s = close[symbol].dropna()
    if len(s) <= n:
        return 0.0
    return _safe_float(s.iloc[-1] / s.iloc[-1 - n] - 1.0)


def _z_last(series: pd.Series, window: int) -> float:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if len(s) < max(20, window // 2):
        return 0.0
    sample = s.tail(window)
    sd = _safe_float(sample.std(ddof=1))
    if sd <= 0.0:
        return 0.0
    return _safe_float((sample.iloc[-1] - sample.mean()) / sd)


def _normalize_capped(raw: dict[str, float], symbols: list[str], cap: float) -> dict[str, float]:
    clean = {s: max(0.0, _safe_float(raw.get(s, 0.0))) for s in symbols}
    gross = sum(clean.values())
    if gross <= 0.0:
        return {s: (1.0 if s == "SHY" and s in symbols else 0.0) for s in symbols}
    w = {s: v / gross for s, v in clean.items()}
    for _ in range(5):
        excess = sum(max(0.0, v - cap) for v in w.values())
        w = {s: min(v, cap) for s, v in w.items()}
        uncapped = [s for s, v in w.items() if v < cap - 1e-12]
        denom = sum(w[s] for s in uncapped)
        if excess <= 1e-12 or denom <= 0.0:
            break
        for s in uncapped:
            w[s] += excess * w[s] / denom
    gross2 = sum(w.values())
    return {s: (v / gross2 if gross2 > 0 else 0.0) for s, v in w.items()}


def generate_signals(context: Any) -> dict[str, float]:
    """Return target ETF weights.

    Regime score components:
    1. short/medium and medium/slow realized-volatility term ratios across ETFs;
    2. breadth of ETFs with compressing realized volatility;
    3. SPY downside-volatility surprise and drawdown state; and
    4. defensive asset momentum versus equity momentum.
    """
    symbols = list(getattr(context, "symbols", UNIVERSE) or UNIVERSE)
    prices = getattr(context, "prices", None)
    weights = {s: 0.0 for s in symbols}
    if prices is None or len(prices) < 80:
        return weights

    close = _pivot(prices, "close").reindex(columns=[s for s in symbols if s in UNIVERSE]).ffill()
    if close.empty or "SPY" not in close.columns or len(close.dropna(how="all")) < 80:
        return weights

    p = PARAMS.copy()
    rets = close.pct_change()
    rv10 = _realized_vol(rets, int(p["vol_short"]))
    rv20 = _realized_vol(rets, int(p["vol_medium"]))
    rv60 = _realized_vol(rets, int(p["vol_slow"]))
    available = [s for s in close.columns if s in rv20.index and pd.notna(rv20.get(s))]
    if not available:
        return weights

    short_medium = (rv10 / rv20.replace(0.0, pd.NA)).replace([float("inf"), float("-inf")], pd.NA)
    medium_slow = (rv20 / rv60.replace(0.0, pd.NA)).replace([float("inf"), float("-inf")], pd.NA)
    term_state = (0.55 * short_medium + 0.45 * medium_slow).reindex(available)
    compression_breadth = _safe_float((term_state.dropna() < 0.95).mean())
    expansion_breadth = _safe_float((term_state.dropna() > 1.10).mean())

    spy = close["SPY"].dropna()
    drawdown = 0.0
    if len(spy) >= int(p["drawdown_window"]):
        trailing = spy.tail(int(p["drawdown_window"]))
        drawdown = _safe_float(spy.iloc[-1] / trailing.max() - 1.0)

    spy_rets = rets["SPY"].dropna()
    downside = spy_rets.where(spy_rets < 0.0, 0.0)
    downside_rv = downside.rolling(int(p["downside_window"])).std(ddof=1) * math.sqrt(252)
    downside_surprise = _z_last(downside_rv, 63)

    mom = {s: _ret(close, s, int(p["momentum_window"])) for s in available}
    equity_mom = sum(mom.get(s, 0.0) for s in ["SPY", "QQQ", "IWM"] if s in available) / max(
        1, len([s for s in ["SPY", "QQQ", "IWM"] if s in available])
    )
    defensive_mom = sum(mom.get(s, 0.0) for s in ["TLT", "GLD", "XLU", "SHY"] if s in available) / max(
        1, len([s for s in ["TLT", "GLD", "XLU", "SHY"] if s in available])
    )
    defensive_confirmation = defensive_mom > equity_mom + 0.01

    stress_score = 0.0
    stress_score += max(0.0, expansion_breadth - 0.35) / 0.65
    stress_score += max(0.0, -drawdown - 0.06) / 0.14
    stress_score += max(0.0, downside_surprise) / 3.0
    stress_score += 0.35 if defensive_confirmation else 0.0
    stress_score -= max(0.0, compression_breadth - float(p["breadth_threshold"])) / 0.40
    stress_score = max(0.0, min(1.5, stress_score))

    risk_on = compression_breadth >= float(p["breadth_threshold"]) and drawdown > -0.08 and stress_score < 0.70
    defensive_budget = float(p["defensive_budget"])

    if risk_on:
        candidates = [s for s in RISK_ON if s in available]
        raw = {}
        for s in candidates:
            rv = max(_safe_float(rv20.get(s), 0.20), 0.03)
            raw[s] = max(0.0, mom.get(s, 0.0) + 0.04) / rv + 0.05
        # Keep a stabilizer unless volatility compression is extremely broad.
        if "SHY" in symbols and compression_breadth < 0.80:
            raw["SHY"] = 0.10
    else:
        candidates = [s for s in DEFENSIVE if s in available]
        raw = {}
        for s in candidates:
            rv = max(_safe_float(rv20.get(s), 0.12), 0.02)
            raw[s] = max(0.0, mom.get(s, 0.0) + 0.02) / rv + 0.08
        if "SPY" in available and stress_score < 1.05 and drawdown > -0.16:
            raw["SPY"] = 0.10

    normalized = _normalize_capped(raw, symbols, float(p["max_weight"]))

    # Ex-ante turnover brake proxy: add SHY ballast in stressed defensive states to
    # reduce daily allocation jumps; qfa itself has no previous-weight context.
    if not risk_on and "SHY" in symbols:
        for s in normalized:
            normalized[s] *= defensive_budget
        normalized["SHY"] = normalized.get("SHY", 0.0) + (1.0 - defensive_budget)
        gross = sum(normalized.values())
        if gross > 0:
            normalized = {s: v / gross for s, v in normalized.items()}

    return {s: float(normalized.get(s, 0.0)) for s in symbols}
