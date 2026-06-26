"""AR-071 ETF realized-skew crash/rebound breadth allocator.

qfa contract: expose generate_signals(context) returning target weights.
Uses only OHLCV bars supplied by qfa/Alpaca. No external data, CSV, daemon, or orders.
"""
from __future__ import annotations

import math

import pandas as pd

UNIVERSE = ["SPY", "QQQ", "IWM", "XLV", "XLY", "XLE", "XLU", "XLP", "TLT", "IEF", "GLD", "HYG", "LQD", "SHY"]
RISK_ASSETS = ["SPY", "QQQ", "IWM", "XLV", "XLY", "XLE", "HYG"]
DEFENSIVE_CASH = "SHY"

PARAMS = {
    "skew_window": 63,
    "fast_skew_window": 21,
    "vol_window": 21,
    "vol_z_window": 126,
    "crash_threshold_sigma": 1.5,
    "min_crash_breadth": 0.32,
    "min_rebound_breadth": 0.36,
    "rebound_lookback": 3,
    "reversal_lookback": 5,
    "holding_days": 5,
    "top_n": 4,
    "single_name_cap": 0.28,
    "max_gross": 1.0,
    "min_history": 170,
}


def _price_matrix(context) -> pd.DataFrame:
    prices = context.prices.copy()
    if prices.empty or "timestamp" not in prices.columns:
        return pd.DataFrame()
    prices["timestamp"] = pd.to_datetime(prices["timestamp"], utc=True)
    cols = [s for s in UNIVERSE if s in context.symbols]
    close = (
        prices[prices["symbol"].isin(cols)]
        .pivot(index="timestamp", columns="symbol", values="close")
        .sort_index()
        .ffill()
    )
    return close.dropna(axis=1, how="all")


def _z_last(series: pd.Series, window: int) -> float:
    tail = series.dropna().iloc[-window:]
    if len(tail) < max(20, window // 3):
        return 0.0
    sd = float(tail.std(ddof=1))
    if not math.isfinite(sd) or sd == 0.0:
        return 0.0
    return float((tail.iloc[-1] - tail.mean()) / sd)


def _downside_skew(x: pd.Series) -> float:
    # Daily downside-tail proxy: skew of losses with upside clipped to zero.
    y = x.clip(upper=0.0).dropna()
    if len(y) < 12:
        return 0.0
    val = float(y.skew())
    return val if math.isfinite(val) else 0.0


def _active_breadth_event(rets: pd.DataFrame) -> bool:
    p = PARAMS
    if len(rets) < p["min_history"]:
        return False
    cols = [c for c in UNIVERSE if c in rets.columns]
    if len(cols) < 6:
        return False
    vol = rets[cols].rolling(p["vol_window"]).std(ddof=1).replace(0.0, pd.NA)
    crash = rets[cols] < (-p["crash_threshold_sigma"] * vol)
    crash_breadth = crash.sum(axis=1) / float(len(cols))
    rebound_breadth = (rets[cols].rolling(p["rebound_lookback"]).sum() > 0.0).sum(axis=1) / float(len(cols))
    broad = rets[[c for c in ("SPY", "QQQ", "IWM") if c in rets.columns] or cols].mean(axis=1)
    rv = broad.rolling(p["vol_window"]).std(ddof=1) * math.sqrt(252)
    lookback = min(p["holding_days"], len(rets))
    for i in range(1, lookback + 1):
        cb = float(crash_breadth.iloc[-i]) if math.isfinite(float(crash_breadth.iloc[-i])) else 0.0
        rb = float(rebound_breadth.iloc[-1]) if math.isfinite(float(rebound_breadth.iloc[-1])) else 0.0
        vz = _z_last(rv.iloc[: len(rv) - i + 1], p["vol_z_window"])
        # Require a recent broad crash and either current rebound breadth or a vol shock.
        if cb >= p["min_crash_breadth"] and (rb >= p["min_rebound_breadth"] or vz >= 1.0):
            return True
    return False


def _rank_relief_candidates(close: pd.DataFrame, rets: pd.DataFrame) -> dict[str, float]:
    p = PARAMS
    candidates = [s for s in RISK_ASSETS if s in close.columns]
    rows: list[tuple[str, float]] = []
    broad = rets[[c for c in ("SPY", "QQQ", "IWM") if c in rets.columns] or list(rets.columns)].mean(axis=1)
    broad_shock = max(0.0, _z_last(broad.rolling(p["vol_window"]).std(ddof=1), p["vol_z_window"]))
    for s in candidates:
        r = rets[s].dropna()
        px = close[s].dropna()
        if len(r) < p["skew_window"] + 5 or len(px) < p["skew_window"] + 5:
            continue
        skew_slow = _downside_skew(r.iloc[-p["skew_window"] :])
        skew_fast = _downside_skew(r.iloc[-p["fast_skew_window"] :])
        ret5 = float(px.iloc[-1] / px.iloc[-p["reversal_lookback"]] - 1.0)
        ret3 = float(px.iloc[-1] / px.iloc[-p["rebound_lookback"]] - 1.0)
        dd63 = float(px.iloc[-1] / px.iloc[-63:].max() - 1.0) if len(px) >= 63 else 0.0
        vol = float(r.iloc[-p["vol_window"] :].std(ddof=1))
        # Preference: capitulated names (negative short return/drawdown and downside skew) that have begun to rebound.
        capitulation = -ret5 + max(0.0, -dd63) + max(0.0, -skew_slow) * 0.015 + max(0.0, -skew_fast) * 0.01
        rebound = max(0.0, ret3) * 1.5
        score = capitulation + rebound + 0.05 * broad_shock - 0.25 * max(0.0, vol - 0.035)
        if math.isfinite(score):
            rows.append((s, score))
    rows.sort(key=lambda item: item[1], reverse=True)
    chosen = [s for s, score in rows[: p["top_n"]] if score > 0.0]
    if not chosen:
        return {DEFENSIVE_CASH: 1.0} if DEFENSIVE_CASH in close.columns else {}
    raw = min(p["single_name_cap"], p["max_gross"] / len(chosen))
    weights = {s: raw for s in chosen}
    gross = sum(abs(v) for v in weights.values())
    if gross < p["max_gross"] and DEFENSIVE_CASH in close.columns:
        weights[DEFENSIVE_CASH] = p["max_gross"] - gross
    return weights


def generate_signals(context) -> dict[str, float]:
    close = _price_matrix(context)
    if close.empty or len(close) < PARAMS["min_history"]:
        return {DEFENSIVE_CASH: 1.0} if DEFENSIVE_CASH in context.symbols else {}
    rets = close.pct_change().dropna(how="all")
    if _active_breadth_event(rets):
        return _rank_relief_candidates(close, rets)
    return {DEFENSIVE_CASH: 1.0} if DEFENSIVE_CASH in close.columns else {}
