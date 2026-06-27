"""AR-077 ETF trend-breadth regime allocator.

Research-only qfa alpha contract: generate_signals(context) -> dict[str, float].
Uses only historical OHLCV bars supplied by qfa/Alpaca. The mechanism is
cross-asset ETF trend breadth and downside participation, intentionally
separate from AR-069's mega-cap post-gap continuation basket.
"""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

UNIVERSE = ["SPY", "QQQ", "IWM", "TLT", "IEF", "SHY", "GLD", "XLU", "XLE", "XLV"]
RISK_ASSETS = ["SPY", "QQQ", "IWM", "XLE", "XLV"]
DEFENSIVE_ASSETS = ["TLT", "IEF", "SHY", "GLD", "XLU"]
PARAMS = {
    "fast_trend": 20,
    "mid_trend": 60,
    "slow_trend": 120,
    "vol_lookback": 20,
    "downside_lookback": 20,
    "drawdown_window": 126,
    "risk_on_breadth": 0.60,
    "risk_off_breadth": 0.40,
    "max_weight": 0.35,
    "defensive_floor": 0.15,
    "stress_equity_stub": 0.08,
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


def _ret(close: pd.DataFrame, symbol: str, lookback: int) -> float:
    if symbol not in close:
        return 0.0
    s = close[symbol].dropna()
    if len(s) <= lookback:
        return 0.0
    return _safe_float(s.iloc[-1] / s.iloc[-1 - lookback] - 1.0)


def _cap_normalize(raw: dict[str, float], symbols: list[str], cap: float) -> dict[str, float]:
    clean = {s: max(0.0, _safe_float(raw.get(s, 0.0))) for s in symbols}
    gross = sum(clean.values())
    if gross <= 0.0:
        return {s: (1.0 if s == "SHY" and s in symbols else 0.0) for s in symbols}
    weights = {s: v / gross for s, v in clean.items()}
    for _ in range(8):
        excess = sum(max(0.0, v - cap) for v in weights.values())
        weights = {s: min(v, cap) for s, v in weights.items()}
        room = {s: cap - v for s, v in weights.items() if v < cap - 1e-12}
        room_total = sum(room.values())
        if excess <= 1e-12 or room_total <= 0.0:
            break
        for s, r in room.items():
            weights[s] += excess * r / room_total
    final_gross = sum(weights.values())
    return {s: (v / final_gross if final_gross > 0 else 0.0) for s, v in weights.items()}


def generate_signals(context: Any) -> dict[str, float]:
    """Return long-only ETF weights from trend breadth and downside participation.

    Breadth is the fraction of available ETFs with positive 20/60/120-day
    composite trend. Downside participation is the fraction of risk assets
    participating in recent negative SPY days. Risk-on regimes own diversified
    positive-trend equities/sectors with defensive ballast; deteriorating
    regimes rotate toward duration/cash/gold/utility sleeves.
    """
    symbols = list(getattr(context, "symbols", UNIVERSE) or UNIVERSE)
    prices = getattr(context, "prices", None)
    out = {s: 0.0 for s in symbols}
    if prices is None or len(prices) < 140:
        return out

    close = _pivot(prices, "close").reindex(columns=[s for s in symbols if s in UNIVERSE]).ffill()
    if close.empty or "SPY" not in close or len(close.dropna(how="all")) < 140:
        return out
    available = [s for s in close.columns if close[s].dropna().shape[0] >= 130]
    if not available:
        return out

    p = PARAMS.copy()
    trend_scores: dict[str, float] = {}
    for s in available:
        r20 = _ret(close, s, int(p["fast_trend"]))
        r60 = _ret(close, s, int(p["mid_trend"]))
        r120 = _ret(close, s, int(p["slow_trend"]))
        trend_scores[s] = 0.35 * r20 + 0.40 * r60 + 0.25 * r120
    breadth = sum(v > 0.0 for v in trend_scores.values()) / max(1, len(trend_scores))
    risk_breadth = sum(trend_scores.get(s, 0.0) > 0.0 for s in RISK_ASSETS if s in available) / max(1, len([s for s in RISK_ASSETS if s in available]))

    rets = close.pct_change().dropna(how="all")
    recent = rets.tail(int(p["downside_lookback"]))
    spy_down = recent["SPY"] < 0 if "SPY" in recent else pd.Series(dtype=bool)
    downside_participation = 0.0
    if len(recent) and spy_down.any():
        parts = []
        for s in [x for x in RISK_ASSETS if x in recent.columns and x != "SPY"]:
            parts.append(float((recent.loc[spy_down, s] < 0).mean()))
        downside_participation = sum(parts) / len(parts) if parts else 0.0

    spy = close["SPY"].dropna()
    trailing = spy.tail(int(p["drawdown_window"]))
    drawdown = _safe_float(spy.iloc[-1] / trailing.max() - 1.0) if len(trailing) else 0.0
    rv20 = recent.std(ddof=1) * math.sqrt(252) if len(recent) > 2 else pd.Series(dtype=float)

    stress = 0.0
    stress += max(0.0, float(p["risk_on_breadth"]) - breadth) / float(p["risk_on_breadth"])
    stress += max(0.0, downside_participation - 0.55) / 0.45
    stress += max(0.0, -drawdown - 0.06) / 0.18
    stress = max(0.0, min(1.5, stress))

    risk_on = breadth >= float(p["risk_on_breadth"]) and risk_breadth >= 0.60 and stress < 0.75
    transition = (float(p["risk_off_breadth"]) <= breadth < float(p["risk_on_breadth"])) or (0.75 <= stress < 1.05)

    raw: dict[str, float] = {}
    if risk_on:
        for s in [x for x in RISK_ASSETS if x in available]:
            vol = max(_safe_float(rv20.get(s), 0.18), 0.04)
            raw[s] = max(0.0, trend_scores.get(s, 0.0) + 0.03) / vol + 0.05
        for s in ["IEF", "GLD", "XLU", "SHY"]:
            if s in available:
                raw[s] = max(raw.get(s, 0.0), float(p["defensive_floor"]) / 4.0)
    elif transition:
        for s in [x for x in RISK_ASSETS if x in available]:
            vol = max(_safe_float(rv20.get(s), 0.20), 0.04)
            raw[s] = 0.45 * max(0.0, trend_scores.get(s, 0.0) + 0.02) / vol
        for s in [x for x in DEFENSIVE_ASSETS if x in available]:
            vol = max(_safe_float(rv20.get(s), 0.12), 0.025)
            raw[s] = max(0.0, trend_scores.get(s, 0.0) + 0.015) / vol + 0.08
    else:
        for s in [x for x in DEFENSIVE_ASSETS if x in available]:
            vol = max(_safe_float(rv20.get(s), 0.10), 0.02)
            raw[s] = max(0.0, trend_scores.get(s, 0.0) + 0.012) / vol + 0.10
        if "SPY" in available and drawdown > -0.18:
            raw["SPY"] = float(p["stress_equity_stub"])

    weights = _cap_normalize(raw, symbols, float(p["max_weight"]))
    return {s: float(weights.get(s, 0.0)) for s in symbols}
