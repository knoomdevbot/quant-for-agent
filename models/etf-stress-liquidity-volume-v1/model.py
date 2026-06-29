"""AR-043 ETF stress liquidity-volume dislocation detector.

QFA-compatible alpha using only daily OHLCV bars.  The model does not use
overnight-gap reversal.  It estimates whether recent cross-ETF abnormal dollar
volume, high-low range expansion, and poor close-location values indicate a
liquidity-stress dislocation, then shifts a long-only allocation between risk
assets and defensive ETF sleeves.
"""

from __future__ import annotations

import math
from typing import Dict, Iterable

import pandas as pd

UNIVERSE = ("SPY", "QQQ", "IWM", "TLT", "GLD", "XLU", "XLE")
RISK_ASSETS = ("SPY", "QQQ", "IWM", "XLE")
DEFENSIVE_ASSETS = ("TLT", "GLD", "XLU")

MIN_HISTORY = 130
FAST_WINDOW = 20
BASELINE_WINDOW = 90
TREND_WINDOW = 40
VOL_WINDOW = 40
MAX_SINGLE_WEIGHT = 0.36
MIN_GROSS = 0.80


def _safe_float(value, default: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return default
    return out if math.isfinite(out) else default


def _clip(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _zscore(current: float, hist: pd.Series) -> float:
    hist = hist.replace([math.inf, -math.inf], pd.NA).dropna()
    if len(hist) < 30:
        return 0.0
    mu = _safe_float(hist.mean())
    sd = _safe_float(hist.std(ddof=1))
    if sd <= 1e-12:
        return 0.0
    return _clip((current - mu) / sd, -3.0, 3.0)


def _ret(close: pd.DataFrame, symbol: str, window: int) -> float:
    if symbol not in close.columns:
        return 0.0
    s = close[symbol].dropna()
    if len(s) <= window or s.iloc[-window - 1] <= 0:
        return 0.0
    return _safe_float(s.iloc[-1] / s.iloc[-window - 1] - 1.0)


def _vol(close: pd.DataFrame, symbol: str, window: int) -> float:
    if symbol not in close.columns:
        return 0.0
    r = close[symbol].dropna().pct_change().dropna().tail(window)
    if len(r) < 10:
        return 0.0
    return _safe_float(r.std(ddof=1) * math.sqrt(252.0))


def _basket_avg(values: Iterable[float]) -> float:
    vals = [v for v in values if math.isfinite(v)]
    return sum(vals) / len(vals) if vals else 0.0


def _normalize_capped(scores: Dict[str, float], budget: float) -> Dict[str, float]:
    positives = {k: max(0.0, _safe_float(v)) for k, v in scores.items()}
    if budget <= 0 or sum(positives.values()) <= 0:
        return {k: 0.0 for k in scores}
    weights = {k: budget * v / sum(positives.values()) for k, v in positives.items()}
    # Simple iterative cap; excess is redistributed among uncapped positive names.
    for _ in range(5):
        excess = sum(max(0.0, w - MAX_SINGLE_WEIGHT) for w in weights.values())
        if excess <= 1e-12:
            break
        capped = {k for k, w in weights.items() if w >= MAX_SINGLE_WEIGHT}
        for k in capped:
            weights[k] = min(weights[k], MAX_SINGLE_WEIGHT)
        uncapped = {k: positives[k] for k in weights if k not in capped and positives[k] > 0}
        total = sum(uncapped.values())
        if total <= 0:
            break
        for k, v in uncapped.items():
            weights[k] += excess * v / total
    return weights


def generate_signals(context) -> dict[str, float]:
    symbols = list(context.symbols)
    if context.prices is None or context.prices.empty:
        return {s: 0.0 for s in symbols}

    prices = context.prices.copy()
    prices["timestamp"] = pd.to_datetime(prices["timestamp"], utc=True)
    prices = prices[prices["symbol"].isin(UNIVERSE)].sort_values(["timestamp", "symbol"])

    close = prices.pivot(index="timestamp", columns="symbol", values="close").sort_index().ffill()
    high = prices.pivot(index="timestamp", columns="symbol", values="high").sort_index().ffill()
    low = prices.pivot(index="timestamp", columns="symbol", values="low").sort_index().ffill()
    volume = prices.pivot(index="timestamp", columns="symbol", values="volume").sort_index().ffill()
    if len(close) < MIN_HISTORY:
        return {s: 0.0 for s in symbols}

    available = [s for s in symbols if s in UNIVERSE and s in close.columns]
    if len(available) < 5:
        return {s: 0.0 for s in symbols}

    stress_components: Dict[str, float] = {}
    clv_components: Dict[str, float] = {}
    for s in available:
        c = close[s].dropna()
        h = high[s].reindex(c.index).ffill()
        lows = low[s].reindex(c.index).ffill()
        v = volume[s].reindex(c.index).ffill()
        if len(c) < MIN_HISTORY:
            continue
        hl_range = ((h - lows) / c.shift(1)).replace([math.inf, -math.inf], pd.NA).dropna()
        dollar_vol = (c * v).replace([math.inf, -math.inf], pd.NA).dropna()
        range_z = _zscore(_safe_float(hl_range.iloc[-1]), hl_range.iloc[-BASELINE_WINDOW - 1 : -1])
        dvol_z = _zscore(_safe_float(math.log(max(dollar_vol.iloc[-1], 1.0))), dollar_vol.apply(lambda x: math.log(max(float(x), 1.0))).iloc[-BASELINE_WINDOW - 1 : -1])
        denom = max(_safe_float(h.iloc[-1] - lows.iloc[-1]), 1e-9)
        close_location = _clip(_safe_float((c.iloc[-1] - lows.iloc[-1]) / denom), 0.0, 1.0)
        poor_close = 1.0 - close_location
        # Stress rises with abnormal trading demand and wide ranges, especially if
        # shares close near the day's low.  This deliberately ignores open/gap data.
        stress = 0.42 * max(0.0, range_z) + 0.38 * max(0.0, dvol_z) + 0.20 * poor_close
        stress_components[s] = _clip(stress / 2.2, 0.0, 1.0)
        clv_components[s] = close_location

    if not stress_components:
        return {s: 0.0 for s in symbols}

    equity_stress = _basket_avg(stress_components.get(s, 0.0) for s in RISK_ASSETS if s in stress_components)
    defensive_stress = _basket_avg(stress_components.get(s, 0.0) for s in DEFENSIVE_ASSETS if s in stress_components)
    breadth = sum(1 for v in stress_components.values() if v > 0.55) / max(len(stress_components), 1)
    risk_stress = _clip(0.58 * equity_stress + 0.27 * breadth + 0.15 * max(0.0, equity_stress - defensive_stress), 0.0, 1.0)

    # Strong broad liquidity stress increases defensive budget; calm periods keep
    # meaningful equity exposure.  Gross is slightly reduced during extreme stress.
    risk_off_budget = 0.22 + 0.58 * risk_stress
    risk_on_budget = 0.72 - 0.50 * risk_stress
    gross_target = _clip(risk_off_budget + risk_on_budget - 0.14 * max(0.0, risk_stress - 0.75), MIN_GROSS, 1.0)
    scale = gross_target / max(risk_off_budget + risk_on_budget, 1e-12)
    risk_off_budget *= scale
    risk_on_budget *= scale

    risk_scores: Dict[str, float] = {}
    for s in RISK_ASSETS:
        if s not in available:
            continue
        stress_penalty = stress_components.get(s, 0.0)
        trend = _clip(_ret(close, s, TREND_WINDOW) / 0.08, -1.0, 1.0)
        realized_vol = _vol(close, s, VOL_WINDOW)
        risk_scores[s] = max(0.05, 1.0 + 0.35 * trend - 0.65 * stress_penalty - 0.30 * realized_vol)

    off_scores: Dict[str, float] = {}
    for s in DEFENSIVE_ASSETS:
        if s not in available:
            continue
        trend = _clip(_ret(close, s, TREND_WINDOW) / 0.06, -1.0, 1.0)
        stress_penalty = stress_components.get(s, 0.0)
        clv = clv_components.get(s, 0.5)
        # Prefer defensive instruments with stable liquidity and firm closes.
        off_scores[s] = max(0.05, 1.0 + 0.45 * trend + 0.20 * clv - 0.45 * stress_penalty)

    weights = {s: 0.0 for s in symbols}
    for k, v in _normalize_capped(risk_scores, risk_on_budget).items():
        weights[k] = weights.get(k, 0.0) + v
    for k, v in _normalize_capped(off_scores, risk_off_budget).items():
        weights[k] = weights.get(k, 0.0) + v
    return {s: _safe_float(weights.get(s, 0.0)) for s in symbols}
