"""AR-073 ETF relief-rally exhaustion reversal alpha.

qfa contract: expose generate_signals(context) returning symbol target weights.
Uses only OHLCV bars supplied by qfa/Alpaca. No CSV, daemon, or orders.

Mechanism: after a recent broad ETF stress drawdown followed by a fast relief
rally, short the most over-extended/high-vol risk-on ETFs and fund with lagging
or defensive ETF longs. The signal is explicitly cross-sectional and distinct
from macro state allocators: it keys off recent realized ETF recovery/stretch
rather than a persistent macro drawdown regime.
"""
from __future__ import annotations

import math

import pandas as pd

UNIVERSE = ["SPY", "QQQ", "IWM", "XLE", "XLY", "XLV", "XLP", "XLU", "TLT", "IEF", "GLD", "HYG", "LQD", "SHY"]
RISK_ON = ["QQQ", "IWM", "XLE", "XLY", "SPY", "HYG"]
DEFENSIVE = ["SHY", "IEF", "TLT", "GLD", "XLP", "XLU", "XLV", "LQD"]
ANCHORS = ["SPY", "QQQ", "IWM", "HYG", "XLY", "XLE"]

PARAMS = {
    "min_history": 170,
    "stress_lookback": 63,
    "recovery_lookback": 10,
    "short_stretch_window": 21,
    "vol_window": 21,
    "vol_z_window": 126,
    "broad_drawdown_trigger": -0.055,
    "recovery_trigger": 0.030,
    "risk_def_spread_trigger": 0.018,
    "min_relief_breadth": 0.42,
    "top_short_n": 3,
    "top_long_n": 3,
    "max_gross": 1.0,
    "net_bias": -0.10,
    "single_name_cap": 0.24,
    "cash_symbol": "SHY",
}


def _safe_float(x: object, default: float = 0.0) -> float:
    try:
        y = float(x)
    except Exception:
        return default
    return y if math.isfinite(y) else default


def _price_matrix(context) -> pd.DataFrame:
    if context.prices is None or context.prices.empty or "timestamp" not in context.prices.columns:
        return pd.DataFrame()
    prices = context.prices.copy()
    prices["timestamp"] = pd.to_datetime(prices["timestamp"], utc=True)
    as_of = pd.Timestamp(context.as_of)
    as_of = as_of.tz_convert("UTC") if as_of.tzinfo else as_of.tz_localize("UTC")
    cols = [s for s in UNIVERSE if s in set(context.symbols)]
    close = (
        prices[prices["symbol"].isin(cols) & (prices["timestamp"] <= as_of)]
        .pivot(index="timestamp", columns="symbol", values="close")
        .sort_index()
        .ffill()
    )
    return close.dropna(axis=1, how="all")


def _z_last(series: pd.Series, window: int) -> float:
    tail = series.dropna().iloc[-window:]
    if len(tail) < max(20, window // 3):
        return 0.0
    sd = _safe_float(tail.std(ddof=1))
    if sd <= 1e-10:
        return 0.0
    return max(-4.0, min(4.0, _safe_float((tail.iloc[-1] - tail.mean()) / sd)))


def _drawdown(px: pd.Series, lookback: int) -> float:
    tail = px.dropna().iloc[-lookback:]
    if len(tail) < max(10, lookback // 3):
        return 0.0
    high = _safe_float(tail.max())
    last = _safe_float(tail.iloc[-1])
    return last / high - 1.0 if high > 0 else 0.0


def _relief_event(close: pd.DataFrame, rets: pd.DataFrame) -> tuple[bool, float]:
    p = PARAMS
    anchors = [s for s in ANCHORS if s in close.columns]
    defs = [s for s in DEFENSIVE if s in close.columns]
    if len(anchors) < 3 or len(close) < p["min_history"]:
        return False, 0.0

    broad = close[anchors].mean(axis=1)
    recent_dd = _drawdown(broad, p["stress_lookback"])
    ret10 = _safe_float(broad.iloc[-1] / broad.iloc[-p["recovery_lookback"]] - 1.0) if len(broad) > p["recovery_lookback"] else 0.0
    relief_breadth = _safe_float((close[anchors].pct_change(p["recovery_lookback"]).iloc[-1] > 0.0).mean())
    risk_ret = _safe_float(close[anchors].pct_change(p["recovery_lookback"]).iloc[-1].mean())
    def_ret = _safe_float(close[defs].pct_change(p["recovery_lookback"]).iloc[-1].mean()) if defs else 0.0
    spread = risk_ret - def_ret
    broad_vol = rets[anchors].mean(axis=1).rolling(p["vol_window"]).std(ddof=1) * math.sqrt(252)
    vol_z = max(0.0, _z_last(broad_vol, p["vol_z_window"]))

    trigger = (
        recent_dd <= p["broad_drawdown_trigger"]
        and ret10 >= p["recovery_trigger"]
        and spread >= p["risk_def_spread_trigger"]
        and relief_breadth >= p["min_relief_breadth"]
    )
    # Slightly softer gate during realized-volatility shocks to catch faster V-shaped relief.
    trigger = trigger or (
        recent_dd <= p["broad_drawdown_trigger"] * 0.75
        and ret10 >= p["recovery_trigger"] * 0.85
        and spread > 0.0
        and relief_breadth >= 0.50
        and vol_z >= 0.8
    )
    intensity = min(1.0, max(0.0, (-recent_dd - 0.03) / 0.12 + ret10 / 0.12 + spread / 0.08 + vol_z / 6.0) / 3.0)
    return trigger, max(0.35, intensity) if trigger else 0.0


def _rank_scores(close: pd.DataFrame, rets: pd.DataFrame) -> tuple[list[tuple[str, float]], list[tuple[str, float]]]:
    p = PARAMS
    short_rows: list[tuple[str, float]] = []
    long_rows: list[tuple[str, float]] = []
    all_cols = [s for s in UNIVERSE if s in close.columns]
    xret = close[all_cols].pct_change(p["recovery_lookback"]).iloc[-1]
    median_xret = _safe_float(xret.median())
    for s in [x for x in RISK_ON if x in close.columns]:
        px = close[s].dropna()
        r = rets[s].dropna()
        if len(px) < p["min_history"] or len(r) < p["vol_window"]:
            continue
        ret10 = _safe_float(px.iloc[-1] / px.iloc[-p["recovery_lookback"]] - 1.0)
        ret21 = _safe_float(px.iloc[-1] / px.iloc[-p["short_stretch_window"]] - 1.0)
        vol = _safe_float(r.iloc[-p["vol_window"] :].std(ddof=1))
        dd63 = _drawdown(px, p["stress_lookback"])
        stretch_z = _z_last(px.pct_change(p["recovery_lookback"]), p["vol_z_window"])
        score = 1.5 * (ret10 - median_xret) + 0.7 * ret21 + 0.6 * max(0.0, stretch_z) + 0.4 * vol + 0.6 * max(0.0, -dd63)
        if score > 0:
            short_rows.append((s, score))
    for s in [x for x in DEFENSIVE if x in close.columns]:
        px = close[s].dropna()
        r = rets[s].dropna()
        if len(px) < p["min_history"] or len(r) < p["vol_window"]:
            continue
        ret10 = _safe_float(px.iloc[-1] / px.iloc[-p["recovery_lookback"]] - 1.0)
        vol = _safe_float(r.iloc[-p["vol_window"] :].std(ddof=1))
        dd63 = _drawdown(px, p["stress_lookback"])
        # Prefer stable laggards and defensive assets that did not participate in relief.
        score = 0.7 * (median_xret - ret10) + 0.25 * max(0.0, -dd63) - 0.25 * vol
        if s in ("SHY", "IEF", "XLP", "XLU"):
            score += 0.025
        long_rows.append((s, score))
    short_rows.sort(key=lambda x: x[1], reverse=True)
    long_rows.sort(key=lambda x: x[1], reverse=True)
    return short_rows, long_rows


def generate_signals(context) -> dict[str, float]:
    close = _price_matrix(context)
    if close.empty or len(close) < PARAMS["min_history"]:
        return {PARAMS["cash_symbol"]: 1.0} if PARAMS["cash_symbol"] in getattr(context, "symbols", []) else {}
    rets = close.pct_change().dropna(how="all")
    active, intensity = _relief_event(close, rets)
    if not active:
        return {PARAMS["cash_symbol"]: 1.0} if PARAMS["cash_symbol"] in close.columns else {}

    shorts, longs = _rank_scores(close, rets)
    shorts = shorts[: PARAMS["top_short_n"]]
    longs = longs[: PARAMS["top_long_n"]]
    if not shorts or not longs:
        return {PARAMS["cash_symbol"]: 1.0} if PARAMS["cash_symbol"] in close.columns else {}

    short_budget = min(0.55, 0.45 + max(0.0, -PARAMS["net_bias"]) / 2.0) * intensity
    long_budget = min(0.45, 0.40 + max(0.0, PARAMS["net_bias"]) / 2.0) * intensity
    cap = PARAMS["single_name_cap"]

    def allocate(rows: list[tuple[str, float]], budget: float, sign: float) -> dict[str, float]:
        total_score = sum(max(0.0, score) for _, score in rows) or float(len(rows))
        out: dict[str, float] = {}
        for sym, score in rows:
            raw = budget * (max(0.0, score) / total_score if total_score else 1.0 / len(rows))
            out[sym] = sign * min(cap, raw)
        return out

    weights: dict[str, float] = {}
    weights.update(allocate(shorts, short_budget, -1.0))
    for sym, val in allocate(longs, long_budget, 1.0).items():
        weights[sym] = weights.get(sym, 0.0) + val
    gross = sum(abs(v) for v in weights.values())
    if gross <= 0:
        return {PARAMS["cash_symbol"]: 1.0} if PARAMS["cash_symbol"] in close.columns else {}
    if gross < PARAMS["max_gross"] and PARAMS["cash_symbol"] in close.columns and weights.get(PARAMS["cash_symbol"], 0.0) >= 0.0:
        weights[PARAMS["cash_symbol"]] = weights.get(PARAMS["cash_symbol"], 0.0) + (PARAMS["max_gross"] - gross) * 0.25
    # qfa will gross-normalize; return already capped sparse targets.
    return {s: _safe_float(v) for s, v in weights.items() if abs(_safe_float(v)) > 1e-8}
