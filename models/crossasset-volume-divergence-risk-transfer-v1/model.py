"""AR-081 cross-asset ETF volume-divergence risk-transfer allocator.

Research-only qfa alpha contract: expose generate_signals(context) -> dict[str, float].
Uses only OHLCV bars supplied by qfa/Alpaca. The mechanism is cross-asset
relative dollar-volume divergence among risk-on equity ETFs, defensive ETFs,
credit ETFs, and sector risk-transfer sleeves.
"""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

UNIVERSE = ["SPY", "QQQ", "IWM", "TLT", "IEF", "GLD", "HYG", "LQD", "SHY", "XLE", "XLU", "XLV"]
RISK_ON = ["SPY", "QQQ", "IWM", "XLE", "XLV"]
DEFENSIVE = ["TLT", "IEF", "GLD", "XLU", "SHY"]
CREDIT = ["HYG", "LQD"]
PARAMS = {
    "volume_fast": 20,
    "volume_slow": 60,
    "trend_lookback": 20,
    "vol_lookback": 20,
    "spread_threshold": 1.0,
    "credit_threshold": 0.45,
    "max_weight": 0.35,
    "gross_target": 1.0,
    "safe_weight": 0.10,
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


def _zscore(series: pd.Series, fast: int, slow: int) -> float:
    clean = series.dropna()
    if len(clean) < slow + 5:
        return 0.0
    base = clean.tail(slow)
    mu = _safe_float(base.mean())
    sd = _safe_float(base.std(ddof=1))
    if sd <= 1e-12:
        return 0.0
    return max(-4.0, min(4.0, (_safe_float(clean.tail(fast).mean()) - mu) / sd))


def _ret(close: pd.DataFrame, symbol: str, lookback: int) -> float:
    if symbol not in close:
        return 0.0
    s = close[symbol].dropna()
    if len(s) <= lookback:
        return 0.0
    return _safe_float(s.iloc[-1] / s.iloc[-1 - lookback] - 1.0)


def _cap_and_scale(raw: dict[str, float], symbols: list[str], cap: float, gross_target: float) -> dict[str, float]:
    weights = {s: max(0.0, _safe_float(raw.get(s, 0.0))) for s in symbols}
    gross = sum(weights.values())
    if gross <= 1e-12:
        return {s: (min(cap, gross_target) if s == "SHY" and s in symbols else 0.0) for s in symbols}
    weights = {s: v * gross_target / gross for s, v in weights.items()}
    for _ in range(10):
        excess = sum(max(0.0, v - cap) for v in weights.values())
        weights = {s: min(v, cap) for s, v in weights.items()}
        room = {s: cap - v for s, v in weights.items() if v < cap - 1e-12}
        room_total = sum(room.values())
        if excess <= 1e-12 or room_total <= 1e-12:
            break
        for s, room_s in room.items():
            weights[s] += excess * room_s / room_total
    gross = sum(weights.values())
    if gross > gross_target and gross > 0:
        weights = {s: v * gross_target / gross for s, v in weights.items()}
    return {s: float(weights.get(s, 0.0)) for s in symbols}


def generate_signals(context: Any) -> dict[str, float]:
    """Return target ETF weights from cross-asset dollar-volume divergence.

    High risk-on relative volume versus defensive volume is interpreted as
    re-risking only when short trend is non-negative. Defensive-volume and
    duration-volume leadership is interpreted as risk transfer away from equities.
    HYG-vs-LQD credit-volume imbalance gates credit risk. Realized volatility
    reduces equity/credit concentration during noisy transfer regimes.
    """
    symbols = list(getattr(context, "symbols", UNIVERSE) or UNIVERSE)
    prices = getattr(context, "prices", None)
    out = {s: 0.0 for s in symbols}
    if prices is None or len(prices) < 80:
        return out

    close = _pivot(prices, "close").reindex(columns=[s for s in symbols if s in UNIVERSE]).ffill()
    volume = _pivot(prices, "volume").reindex(columns=close.columns).ffill()
    if close.empty or volume.empty or "SPY" not in close or len(close.dropna(how="all")) < 70:
        return out
    available = [s for s in close.columns if close[s].dropna().shape[0] >= 65 and volume[s].dropna().shape[0] >= 65]
    if not available:
        return out

    p = PARAMS.copy()
    dollar_volume = (close[available] * volume[available]).replace([math.inf, -math.inf], pd.NA)
    z = {s: _zscore(dollar_volume[s], int(p["volume_fast"]), int(p["volume_slow"])) for s in available}
    trend = {s: _ret(close, s, int(p["trend_lookback"])) for s in available}
    rets = close[available].pct_change().tail(int(p["vol_lookback"]))
    rv = rets.std(ddof=1) * math.sqrt(252) if len(rets) > 3 else pd.Series(dtype=float)

    risk_z = sum(z.get(s, 0.0) for s in RISK_ON if s in available) / max(1, len([s for s in RISK_ON if s in available]))
    def_z = sum(z.get(s, 0.0) for s in DEFENSIVE if s in available) / max(1, len([s for s in DEFENSIVE if s in available]))
    credit_z = _safe_float(z.get("HYG", 0.0) - 0.5 * z.get("LQD", 0.0))
    spread = risk_z - def_z
    spy_trend = trend.get("SPY", 0.0)
    vol_scale = max(0.45, min(1.15, 0.18 / max(_safe_float(rv.get("SPY"), 0.18), 0.05)))

    raw: dict[str, float] = {}
    threshold = float(p["spread_threshold"])
    if spread > threshold and spy_trend > -0.015:
        for s in [x for x in RISK_ON if x in available]:
            score = max(0.0, 0.20 + z.get(s, 0.0) + 3.0 * max(0.0, trend.get(s, 0.0)))
            raw[s] = score * vol_scale / max(_safe_float(rv.get(s), 0.18), 0.06)
        if "HYG" in available and credit_z > -float(p["credit_threshold"]):
            raw["HYG"] = raw.get("HYG", 0.0) + (0.30 + max(0.0, credit_z)) * vol_scale / max(_safe_float(rv.get("HYG"), 0.10), 0.04)
        for s in ["IEF", "GLD", "SHY"]:
            if s in available:
                raw[s] = raw.get(s, 0.0) + float(p["safe_weight"]) / 3.0
    elif spread < -threshold or spy_trend < -0.04:
        for s in ["TLT", "IEF", "GLD", "XLU", "SHY"]:
            if s in available:
                score = 0.25 + max(0.0, z.get(s, 0.0)) + 2.0 * max(0.0, trend.get(s, 0.0))
                raw[s] = score / max(_safe_float(rv.get(s), 0.10), 0.025)
        if "LQD" in available and credit_z < float(p["credit_threshold"]):
            raw["LQD"] = raw.get("LQD", 0.0) + (0.15 + max(0.0, -credit_z)) / max(_safe_float(rv.get("LQD"), 0.08), 0.025)
    else:
        for s in ["SPY", "XLV", "IEF", "GLD", "LQD", "SHY"]:
            if s in available:
                momentum_bonus = 1.0 + 4.0 * max(0.0, trend.get(s, 0.0))
                volume_bonus = 1.0 + 0.20 * max(0.0, z.get(s, 0.0))
                raw[s] = momentum_bonus * volume_bonus / max(_safe_float(rv.get(s), 0.12), 0.035)

    weights = _cap_and_scale(raw, symbols, float(p["max_weight"]), float(p["gross_target"]))
    return {s: float(weights.get(s, 0.0)) for s in symbols}
