"""AR-064 ETF crash-recovery dispersion allocator.

qfa alpha contract: expose generate_signals(context) returning target weights.
Uses only prices supplied by qfa/Alpaca.  No VIXY/convexity sleeve.
"""
from __future__ import annotations

import math

import pandas as pd

UNIVERSE = ["SPY", "QQQ", "IWM", "XLV", "XLU", "XLP", "XLE", "TLT", "IEF", "GLD"]
RISK_ASSETS = ["SPY", "QQQ", "IWM", "XLV", "XLU", "XLP", "XLE"]
DEFENSIVE = ["TLT", "IEF", "GLD", "XLU", "XLP"]

PARAMS = {
    "vol_lookback": 20,
    "vol_z_window": 126,
    "shock_threshold_z": 1.0,
    "dispersion_lookback": 20,
    "dispersion_z_window": 63,
    "compression_threshold_z": -0.20,
    "recovery_lookback": 20,
    "reversal_lookback": 5,
    "holding_days": 10,
    "top_n": 3,
    "single_name_cap": 0.35,
    "max_gross": 1.0,
    "drawdown_exclude": -0.28,
    "min_history": 170,
}


def _price_matrix(context) -> pd.DataFrame:
    prices = context.prices.copy()
    if prices.empty:
        return pd.DataFrame()
    prices["timestamp"] = pd.to_datetime(prices["timestamp"], utc=True)
    close = (
        prices[prices["symbol"].isin([s for s in UNIVERSE if s in context.symbols])]
        .pivot(index="timestamp", columns="symbol", values="close")
        .sort_index()
        .ffill()
    )
    return close.dropna(axis=1, how="all")


def _zscore(series: pd.Series, window: int) -> float:
    tail = series.dropna().iloc[-window:]
    if len(tail) < max(20, window // 3):
        return 0.0
    sd = float(tail.std(ddof=1))
    if not math.isfinite(sd) or sd == 0.0:
        return 0.0
    return float((tail.iloc[-1] - tail.mean()) / sd)


def _shock_and_compression(rets: pd.DataFrame) -> tuple[bool, float, float]:
    p = PARAMS
    stress_cols = [s for s in ("SPY", "QQQ", "IWM") if s in rets.columns]
    if not stress_cols:
        stress_cols = [c for c in RISK_ASSETS if c in rets.columns]
    broad = rets[stress_cols].mean(axis=1)
    rv = broad.rolling(p["vol_lookback"]).std(ddof=1) * math.sqrt(252)
    vol_z = _zscore(rv, p["vol_z_window"])

    universe_cols = [c for c in UNIVERSE if c in rets.columns]
    dispersion = rets[universe_cols].std(axis=1, ddof=1).rolling(p["dispersion_lookback"]).mean()
    disp_z = _zscore(dispersion, p["dispersion_z_window"])
    trigger = vol_z >= p["shock_threshold_z"] and disp_z <= p["compression_threshold_z"]
    return trigger, vol_z, disp_z


def _recent_trigger_active(rets: pd.DataFrame) -> bool:
    p = PARAMS
    if len(rets) < p["min_history"]:
        return False
    lookback = min(p["holding_days"], len(rets) - p["min_history"] + 1)
    if lookback <= 0:
        return False
    for idx in range(lookback):
        sample = rets.iloc[: len(rets) - idx]
        if len(sample) >= p["min_history"] and _shock_and_compression(sample)[0]:
            return True
    return False


def _risk_weights(close: pd.DataFrame, rets: pd.DataFrame) -> dict[str, float]:
    p = PARAMS
    candidates = [s for s in RISK_ASSETS if s in close.columns]
    rows: list[tuple[str, float]] = []
    for s in candidates:
        px = close[s].dropna()
        if len(px) < p["recovery_lookback"] + 2:
            continue
        dd_63 = float(px.iloc[-1] / px.iloc[-63:].max() - 1.0) if len(px) >= 63 else 0.0
        if dd_63 < p["drawdown_exclude"]:
            continue
        ret20 = float(px.iloc[-1] / px.iloc[-p["recovery_lookback"]] - 1.0)
        ret5 = float(px.iloc[-1] / px.iloc[-p["reversal_lookback"]] - 1.0)
        vol20 = float(rets[s].iloc[-20:].std(ddof=1) * math.sqrt(252)) if s in rets else 0.2
        # prefer depressed ETFs that are stabilizing/reversing, penalize high idiosyncratic vol
        score = (-ret20) + 0.75 * ret5 - 0.20 * max(vol20, 0.0)
        rows.append((s, score))
    rows.sort(key=lambda x: x[1], reverse=True)
    selected = [r for r in rows[: p["top_n"]] if r[1] > -0.05]
    if not selected:
        return {}
    raw = {s: max(score, 0.01) for s, score in selected}
    total = sum(raw.values())
    weights = {s: min(p["single_name_cap"], v / total) for s, v in raw.items()}
    gross = sum(weights.values())
    if gross > 0:
        weights = {s: (w / gross) * p["max_gross"] for s, w in weights.items()}
    return weights


def _defensive_weights(close: pd.DataFrame) -> dict[str, float]:
    available = [s for s in DEFENSIVE if s in close.columns]
    if not available:
        return {}
    scores = {}
    for s in available:
        px = close[s].dropna()
        if len(px) < 64:
            continue
        mom = float(px.iloc[-1] / px.iloc[-63] - 1.0)
        dd = float(px.iloc[-1] / px.iloc[-63:].max() - 1.0)
        scores[s] = mom + 0.5 * dd
    if not scores:
        return {available[0]: 1.0}
    keep = sorted(scores.keys(), key=lambda sym: scores[sym], reverse=True)[:2]
    return {s: 1.0 / len(keep) for s in keep}


def generate_signals(context) -> dict[str, float]:
    close = _price_matrix(context)
    if close.empty or len(close) < PARAMS["min_history"]:
        return {}
    close = close[[c for c in UNIVERSE if c in close.columns]].ffill().dropna()
    rets = close.pct_change().dropna()
    if len(rets) < PARAMS["min_history"]:
        return {}

    if _recent_trigger_active(rets):
        weights = _risk_weights(close, rets)
        if weights:
            return {s: float(w) for s, w in weights.items() if s in context.symbols}
    return {s: float(w) for s, w in _defensive_weights(close).items() if s in context.symbols}
