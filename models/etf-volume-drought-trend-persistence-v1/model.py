"""AR-082 ETF volume-drought trend persistence allocator.

Research-only qfa alpha contract: generate_signals(context) -> dict[str, float].
Uses only historical OHLCV bars supplied by qfa/Alpaca. The mechanism is
participation drought plus realized range compression followed by existing
20/60-day trend persistence, intentionally distinct from AR-074's macro-event
liquidity-gap recovery/reversal mechanism.
"""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

UNIVERSE = ["SPY", "QQQ", "IWM", "TLT", "GLD", "XLU", "XLE", "SHY", "HYG", "LQD"]
RISK_ASSETS = ["SPY", "QQQ", "IWM", "XLE", "HYG"]
DEFENSIVE_ASSETS = ["TLT", "GLD", "XLU", "LQD", "SHY"]
PARAMS = {
    "volume_lookback": 126,
    "drought_percentile": 30.0,
    "range_lookback": 20,
    "range_compression_lookback": 126,
    "range_percentile": 40.0,
    "fast_trend": 20,
    "slow_trend": 60,
    "vol_lookback": 20,
    "rebalance_days": 5,
    "max_weight": 0.35,
    "min_signal_assets": 2,
    "cash_fallback_weight": 1.0,
}


def _pivot(prices: pd.DataFrame, field: str) -> pd.DataFrame:
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


def _percentile_rank(series: pd.Series, value: float) -> float:
    s = series.dropna()
    if len(s) == 0:
        return 50.0
    return 100.0 * float((s <= value).mean())


def _cap_normalize(raw: dict[str, float], symbols: list[str], cap: float) -> dict[str, float]:
    clean = {s: max(0.0, _safe_float(raw.get(s, 0.0))) for s in symbols}
    gross = sum(clean.values())
    if gross <= 0.0:
        return {s: (1.0 if s == "SHY" and s in symbols else 0.0) for s in symbols}
    weights = {s: v / gross for s, v in clean.items()}
    for _ in range(10):
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
    """Return long-only ETF weights from volume-drought trend persistence.

    Assets qualify when current participation is in a low trailing-volume
    percentile and true-range/price is compressed, while 20/60-day trend is
    positive. Scores are volatility-scaled and capped. If too few ETFs qualify,
    the allocator falls back to SHY/defensive ETFs instead of forcing risk.
    """
    symbols = list(getattr(context, "symbols", UNIVERSE) or UNIVERSE)
    prices = getattr(context, "prices", None)
    out = {s: 0.0 for s in symbols}
    if prices is None or len(prices) < 150:
        return out

    close = _pivot(prices, "close").reindex(columns=[s for s in symbols if s in UNIVERSE]).ffill()
    high = _pivot(prices, "high").reindex(columns=close.columns).ffill()
    low = _pivot(prices, "low").reindex(columns=close.columns).ffill()
    volume = _pivot(prices, "volume").reindex(columns=close.columns).ffill()
    if close.empty or len(close.dropna(how="all")) < 140:
        return out

    p = PARAMS.copy()
    available = [s for s in close.columns if close[s].dropna().shape[0] >= int(p["volume_lookback"]) + 2]
    if not available:
        return out

    rets = close[available].pct_change()
    rv20 = rets.tail(int(p["vol_lookback"])).std(ddof=1) * math.sqrt(252)
    raw: dict[str, float] = {}
    qualifiers: list[str] = []

    for s in available:
        v = volume[s].dropna()
        c = close[s].dropna()
        if len(v) < int(p["volume_lookback"]) + 2 or len(c) < int(p["slow_trend"]) + 2:
            continue
        vol_hist = v.iloc[-int(p["volume_lookback"])-1:-1]
        vol_rank = _percentile_rank(vol_hist, v.iloc[-1])
        tr_norm = ((high[s] - low[s]) / close[s]).dropna()
        if len(tr_norm) < int(p["range_compression_lookback"]) + 2:
            continue
        recent_range = tr_norm.tail(int(p["range_lookback"])).mean()
        range_hist = tr_norm.iloc[-int(p["range_compression_lookback"])-1:-1]
        range_rank = _percentile_rank(range_hist, recent_range)
        r20 = _ret(close, s, int(p["fast_trend"]))
        r60 = _ret(close, s, int(p["slow_trend"]))
        trend = 0.55 * r20 + 0.45 * r60
        if vol_rank <= float(p["drought_percentile"]) and range_rank <= float(p["range_percentile"]) and trend > 0.0:
            drought_score = (float(p["drought_percentile"]) - vol_rank) / max(float(p["drought_percentile"]), 1.0)
            compression_score = (float(p["range_percentile"]) - range_rank) / max(float(p["range_percentile"]), 1.0)
            vol_scale = max(_safe_float(rv20.get(s), 0.15), 0.025)
            raw[s] = (0.70 * drought_score + 0.30 * compression_score) * max(trend, 0.0) / vol_scale
            qualifiers.append(s)

    if len(qualifiers) < int(p["min_signal_assets"]):
        # Defensive persistence fallback: keep risk low and prefer cash/SHY, but
        # allow defensive ETFs with their own positive 60-day trends.
        raw = {"SHY": float(p["cash_fallback_weight"])} if "SHY" in symbols else {}
        for s in [x for x in DEFENSIVE_ASSETS if x in available and x != "SHY"]:
            trend = 0.40 * _ret(close, s, int(p["fast_trend"])) + 0.60 * _ret(close, s, int(p["slow_trend"]))
            if trend > 0.0:
                raw[s] = max(raw.get(s, 0.0), 0.15 + trend / max(_safe_float(rv20.get(s), 0.10), 0.025))

    weights = _cap_normalize(raw, symbols, float(p["max_weight"]))
    return {s: float(weights.get(s, 0.0)) for s in symbols}
