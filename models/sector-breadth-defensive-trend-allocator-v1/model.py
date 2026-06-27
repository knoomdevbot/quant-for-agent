"""AR-083 sector ETF breadth-confirmed defensive trend allocator.

Research-only qfa alpha contract: expose generate_signals(context) -> dict[str, float].
Uses only historical daily OHLCV bars supplied by qfa/Alpaca. The mechanism is
sector uptrend breadth plus defensive-vs-cyclical leadership, intentionally
separate from AR-075's residual sector dislocation mean reversion.
"""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

UNIVERSE = ["SPY", "QQQ", "IWM", "XLF", "XLK", "XLE", "XLU", "XLV", "XLI", "XLP"]
SECTORS = ["XLF", "XLK", "XLE", "XLU", "XLV", "XLI", "XLP"]
DEFENSIVE = ["XLU", "XLV", "XLP"]
CYCLICAL = ["XLF", "XLK", "XLE", "XLI", "QQQ", "IWM"]
PARAMS = {
    "trend_fast": 20,
    "trend_mid": 60,
    "trend_slow": 126,
    "breadth_threshold": 0.60,
    "defensive_spread_lookback": 60,
    "vol_lookback": 20,
    "spy_trend_lookback": 126,
    "sector_cap": 0.35,
    "risk_on_gross": 1.00,
    "transition_gross": 0.75,
    "risk_off_gross": 0.65,
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


def _cap_normalize(raw: dict[str, float], symbols: list[str], cap: float, gross_target: float) -> dict[str, float]:
    clean = {s: max(0.0, _safe_float(raw.get(s, 0.0))) for s in symbols}
    total = sum(clean.values())
    if total <= 0.0 or gross_target <= 0.0:
        return {s: 0.0 for s in symbols}
    weights = {s: gross_target * v / total for s, v in clean.items()}
    for _ in range(10):
        excess = sum(max(0.0, v - cap) for v in weights.values())
        weights = {s: min(v, cap) for s, v in weights.items()}
        room = {s: cap - v for s, v in weights.items() if v < cap - 1e-12}
        room_total = sum(room.values())
        if excess <= 1e-12 or room_total <= 0.0:
            break
        for s, r in room.items():
            weights[s] += excess * r / room_total
    gross = sum(weights.values())
    if gross > gross_target and gross > 0:
        weights = {s: v * gross_target / gross for s, v in weights.items()}
    return {s: float(weights.get(s, 0.0)) for s in symbols}


def generate_signals(context: Any) -> dict[str, float]:
    """Return long-only target ETF weights from sector breadth and leadership.

    Sector breadth is the fraction of sectors with positive composite 20/60/126d
    trend. Defensive leadership compares equal-weight defensive sectors against
    cyclical/growth sectors over 60d. Strong breadth allocates to leading sector
    momentum ranks; weakening breadth with defensive leadership rotates toward
    XLU/XLV/XLP; a negative SPY 126d trend cuts gross exposure rather than using
    a cash ETF outside the mandated universe.
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
    sectors = [s for s in SECTORS if s in available]
    if len(sectors) < 4:
        return out

    p = PARAMS.copy()
    trend_scores: dict[str, float] = {}
    for s in available:
        r20 = _ret(close, s, int(p["trend_fast"]))
        r60 = _ret(close, s, int(p["trend_mid"]))
        r126 = _ret(close, s, int(p["trend_slow"]))
        trend_scores[s] = 0.30 * r20 + 0.45 * r60 + 0.25 * r126

    sector_breadth = sum(trend_scores.get(s, 0.0) > 0.0 for s in sectors) / max(1, len(sectors))
    spy_trend = _ret(close, "SPY", int(p["spy_trend_lookback"]))
    d_lb = int(p["defensive_spread_lookback"])
    defensive_rets = [_ret(close, s, d_lb) for s in DEFENSIVE if s in available]
    cyclical_rets = [_ret(close, s, d_lb) for s in CYCLICAL if s in available]
    defensive_avg = sum(defensive_rets) / len(defensive_rets) if defensive_rets else 0.0
    cyclical_avg = sum(cyclical_rets) / len(cyclical_rets) if cyclical_rets else 0.0
    defensive_spread = defensive_avg - cyclical_avg

    rets = close[available].pct_change().tail(int(p["vol_lookback"]))
    rv = rets.std(ddof=1) * math.sqrt(252) if len(rets) > 2 else pd.Series(dtype=float)

    raw: dict[str, float] = {}
    breadth_ok = sector_breadth >= float(p["breadth_threshold"])
    spy_ok = spy_trend > 0.0

    if breadth_ok and spy_ok and defensive_spread < 0.025:
        # Broad participation: own top positive sector trends, with small SPY/QQQ/IWM ballast.
        ranked = sorted(sectors, key=lambda s: trend_scores.get(s, 0.0), reverse=True)
        for rank, s in enumerate(ranked[:5]):
            vol = max(_safe_float(rv.get(s), 0.18), 0.05)
            raw[s] = max(0.0, trend_scores.get(s, 0.0) + 0.015) * (1.0 - 0.08 * rank) / vol
        for s in ["SPY", "QQQ", "IWM"]:
            if s in available and trend_scores.get(s, 0.0) > 0.0:
                raw[s] = 0.08 * max(0.0, trend_scores.get(s, 0.0) + 0.01) / max(_safe_float(rv.get(s), 0.18), 0.05)
        gross = float(p["risk_on_gross"])
    elif defensive_spread > -0.01 or not spy_ok:
        # Defensive leadership or poor index trend: rotate to defensive sector ETFs, lower gross if SPY trend is negative.
        for s in [x for x in DEFENSIVE if x in available]:
            vol = max(_safe_float(rv.get(s), 0.14), 0.04)
            raw[s] = max(0.0, trend_scores.get(s, 0.0) + 0.02 + max(0.0, defensive_spread)) / vol + 0.10
        if spy_ok and sector_breadth > 0.45:
            for s in sectors:
                if s not in DEFENSIVE and trend_scores.get(s, 0.0) > 0.0:
                    raw[s] = 0.20 * trend_scores[s] / max(_safe_float(rv.get(s), 0.20), 0.05)
        gross = float(p["risk_off_gross"] if not spy_ok else p["transition_gross"])
    else:
        # Narrow but not defensive-led: hold only strongest confirmed trends at reduced gross.
        ranked = sorted([s for s in sectors if trend_scores.get(s, 0.0) > 0.0], key=lambda s: trend_scores[s], reverse=True)
        for s in ranked[:3]:
            raw[s] = trend_scores[s] / max(_safe_float(rv.get(s), 0.20), 0.05)
        gross = float(p["transition_gross"])

    return _cap_normalize(raw, symbols, float(p["sector_cap"]), gross)
