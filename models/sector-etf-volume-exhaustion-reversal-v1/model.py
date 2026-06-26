"""AR-095 sector ETF post-rebalance volume exhaustion reversal allocator.

QFA contract: expose generate_signals(context) -> dict[str, float].
Uses only historical OHLCV bars supplied by qfa/Alpaca.  The alpha attempts to
fade abnormal sector ETF volume/range exhaustion after failed next-day
follow-through, with an explicit broad-market beta brake/hedge.
"""
from __future__ import annotations

import math
from typing import Any

import pandas as pd

CANDIDATE_UNIVERSE = ["SPY", "QQQ", "IWM", "XLF", "XLK", "XLE", "XLU", "XLV", "XLI", "XLP"]
SELECTED_UNIVERSE = CANDIDATE_UNIVERSE.copy()
SECTORS = ["XLF", "XLK", "XLE", "XLU", "XLV", "XLI", "XLP"]
PARAMS = {
    "volume_short": 20,
    "volume_long": 60,
    "range_lookback": 20,
    "min_history": 90,
    "vol_z_threshold": 1.25,
    "range_z_threshold": 1.00,
    "event_return_threshold": 0.004,
    "close_location_extreme": 0.72,
    "failed_followthrough_threshold": 0.001,
    "sector_cap": 0.35,
    "max_names": 4,
    "market_beta_brake_lookback": 10,
    "market_beta_brake_ret": 0.035,
    "spy_hedge_fraction": 0.35,
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


def _zscore_last(series: pd.Series, lookback: int) -> float:
    s = series.dropna().tail(lookback)
    if len(s) < max(10, lookback // 2):
        return 0.0
    sd = float(s.std(ddof=1))
    if not math.isfinite(sd) or sd <= 1e-12:
        return 0.0
    return _safe_float((float(s.iloc[-1]) - float(s.mean())) / sd)


def _cap_normalize_signed(raw: dict[str, float], symbols: list[str], cap: float) -> dict[str, float]:
    clean = {s: _safe_float(raw.get(s, 0.0)) for s in symbols}
    # Hard cap each single-name signal before gross normalization by qfa.
    for _ in range(3):
        gross = sum(abs(v) for v in clean.values())
        if gross <= 1e-12:
            return {s: 0.0 for s in symbols}
        weights = {s: v / gross for s, v in clean.items()}
        viol = {s: abs(w) for s, w in weights.items() if abs(w) > cap}
        if not viol:
            return weights
        for s in viol:
            clean[s] = math.copysign(cap, clean[s])
    gross = sum(abs(v) for v in clean.values())
    return {s: (v / gross if gross > 1e-12 else 0.0) for s, v in clean.items()}


def generate_signals(context: Any) -> dict[str, float]:
    """Fade abnormal sector ETF volume/range exhaustion after failed follow-through.

    For each selected sector ETF, the model looks for an exhaustion bar one
    session ago: abnormal volume, expanded true range, meaningful close-to-close
    move, and close location near the high/low.  If the latest bar fails to
    follow through, the model takes the opposite sector exposure for the next
    close-to-close period.  A market beta brake suppresses reversal trades that
    fight a strong SPY impulse and adds a partial SPY hedge against sector beta.
    """
    symbols = list(getattr(context, "symbols", SELECTED_UNIVERSE) or SELECTED_UNIVERSE)
    prices = getattr(context, "prices", None)
    out = {s: 0.0 for s in symbols}
    if prices is None or len(prices) < 10:
        return out

    close = _pivot(prices, "close").reindex(columns=[s for s in symbols if s in SELECTED_UNIVERSE]).ffill()
    high = _pivot(prices, "high").reindex(columns=close.columns).ffill()
    low = _pivot(prices, "low").reindex(columns=close.columns).ffill()
    volume = _pivot(prices, "volume").reindex(columns=close.columns).ffill()
    if len(close.dropna(how="all")) < int(PARAMS["min_history"]) or "SPY" not in close:
        return out

    available = [s for s in close.columns if close[s].dropna().shape[0] >= int(PARAMS["min_history"])]
    sectors = [s for s in SECTORS if s in available]
    if not sectors:
        return out

    ret = close.pct_change()
    tr = (high - low) / close.shift(1)
    p = PARAMS
    spy_10d = _safe_float(close["SPY"].iloc[-1] / close["SPY"].iloc[-1 - int(p["market_beta_brake_lookback"])] - 1.0) if len(close["SPY"].dropna()) > int(p["market_beta_brake_lookback"]) else 0.0

    raw: dict[str, float] = {}
    for s in sectors:
        if len(close[s].dropna()) < int(p["min_history"]):
            continue
        # Exhaustion episode measured on t-1; failed follow-through measured on t.
        event_ret = _safe_float(ret[s].iloc[-2])
        follow_ret = _safe_float(ret[s].iloc[-1])
        event_range = _safe_float(tr[s].iloc[-2])
        if event_range <= 0:
            continue
        vol_z = _zscore_last(volume[s].shift(1), int(p["volume_long"]))
        range_z = _zscore_last(tr[s].shift(1), int(p["range_lookback"]))
        clv = _safe_float((close[s].iloc[-2] - low[s].iloc[-2]) / max(high[s].iloc[-2] - low[s].iloc[-2], 1e-9), 0.5)
        direction = 1 if event_ret > 0 else -1
        if abs(event_ret) < float(p["event_return_threshold"]):
            continue
        if vol_z < float(p["vol_z_threshold"]) or range_z < float(p["range_z_threshold"]):
            continue
        if direction > 0 and clv < float(p["close_location_extreme"]):
            continue
        if direction < 0 and clv > 1.0 - float(p["close_location_extreme"]):
            continue
        # Failed follow-through: latest return does not continue event direction.
        if direction * follow_ret > float(p["failed_followthrough_threshold"]):
            continue
        # Market beta brake: do not aggressively short sectors into very strong
        # SPY impulse, or buy sectors into broad-market downside impulse.
        if direction > 0 and spy_10d > float(p["market_beta_brake_ret"]):
            continue
        if direction < 0 and spy_10d < -float(p["market_beta_brake_ret"]):
            continue
        strength = max(0.0, vol_z - float(p["vol_z_threshold"])) + 0.75 * max(0.0, range_z - float(p["range_z_threshold"])) + abs(event_ret) * 10.0
        raw[s] = -direction * strength

    if not raw:
        return out
    # Keep only strongest episodes, then partially hedge residual sector beta with SPY.
    ranked = sorted(raw.items(), key=lambda kv: abs(kv[1]), reverse=True)[: int(p["max_names"])]
    raw = dict(ranked)
    if "SPY" in symbols:
        sector_net = sum(raw.values())
        raw["SPY"] = raw.get("SPY", 0.0) - float(p["spy_hedge_fraction"]) * sector_net
    return _cap_normalize_signed(raw, symbols, float(p["sector_cap"]))
