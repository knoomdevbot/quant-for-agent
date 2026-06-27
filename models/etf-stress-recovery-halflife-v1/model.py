"""AR-055 ETF stress-recovery half-life allocator.

QFA-compatible alpha using daily real OHLCV bars.  It measures whether
volume-normalized high/low range shocks are decaying across 2/5/10 sessions.
Fast stress recovery shifts allocation toward risk ETFs; persistent shocks shift
allocation toward defensive ETFs.  No orders or daemon usage are required.
"""

from __future__ import annotations

import math
from typing import Dict, Iterable

import pandas as pd

UNIVERSE = ("SPY", "QQQ", "IWM", "TLT", "GLD", "XLU", "XLE")
RISK_ASSETS = ("SPY", "QQQ", "IWM", "XLE")
DEFENSIVE_ASSETS = ("TLT", "GLD", "XLU")

MIN_HISTORY = 140
BASELINE_WINDOW = 90
HALFLIFE_WINDOWS = (2, 5, 10)
TREND_WINDOW = 50
VOL_WINDOW = 40
MAX_SINGLE_WEIGHT = 0.36
MIN_GROSS = 0.78


def _safe_float(value, default: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return default
    return out if math.isfinite(out) else default


def _clip(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _mean(values: Iterable[float]) -> float:
    vals = [float(v) for v in values if math.isfinite(float(v))]
    return sum(vals) / len(vals) if vals else 0.0


def _series_zscores(x: pd.Series, window: int) -> pd.Series:
    x = x.replace([math.inf, -math.inf], pd.NA).astype(float)
    mu = x.shift(1).rolling(window, min_periods=max(30, window // 2)).mean()
    sd = x.shift(1).rolling(window, min_periods=max(30, window // 2)).std(ddof=1)
    z = (x - mu) / sd.replace(0.0, pd.NA)
    return z.clip(-4.0, 4.0).fillna(0.0)


def _stress_series(close: pd.Series, high: pd.Series, low: pd.Series, volume: pd.Series) -> pd.Series:
    close = close.dropna().astype(float)
    high = high.reindex(close.index).ffill().astype(float)
    low = low.reindex(close.index).ffill().astype(float)
    volume = volume.reindex(close.index).ffill().astype(float)
    hl_range = ((high - low) / close.shift(1)).replace([math.inf, -math.inf], pd.NA)
    volume_norm_range = (hl_range / volume.rolling(20, min_periods=10).mean().div(1_000_000.0).pow(0.20)).replace(
        [math.inf, -math.inf], pd.NA
    )
    range_z = _series_zscores(volume_norm_range, BASELINE_WINDOW)
    dollar_vol = (close * volume).clip(lower=1.0).apply(math.log)
    dvol_z = _series_zscores(dollar_vol, BASELINE_WINDOW)
    denom = (high - low).abs().clip(lower=1e-9)
    poor_close = (1.0 - ((close - low) / denom).clip(0.0, 1.0)).fillna(0.5)
    stress = 0.52 * range_z.clip(lower=0.0) + 0.28 * dvol_z.clip(lower=0.0) + 0.20 * poor_close
    return (stress / 2.4).clip(0.0, 1.0).fillna(0.0)


def _half_life_proxy(stress: pd.Series) -> tuple[float, float, float]:
    """Return recovery score, persistence score, and current stress.

    Recovery is high when stress has fallen quickly from recent peaks over 2/5/10
    sessions. Persistence is high when current stress remains close to or above
    recent stress. This is a slope/half-life proxy rather than a curve-fit.
    """
    s = stress.dropna().astype(float)
    if len(s) < max(HALFLIFE_WINDOWS) + 5:
        return 0.0, 0.0, 0.0
    current = _safe_float(s.iloc[-1])
    drops = []
    persists = []
    for w in HALFLIFE_WINDOWS:
        prev = _safe_float(s.iloc[-w - 1]) if len(s) > w else current
        recent_peak = _safe_float(s.iloc[-w - 1 :].max())
        denom = max(recent_peak, prev, 0.08)
        drops.append(_clip((recent_peak - current) / denom, -1.0, 1.0))
        persists.append(_clip(current / denom, 0.0, 1.5))
    recovery = _clip(0.25 * drops[0] + 0.45 * drops[1] + 0.30 * drops[2], -1.0, 1.0)
    persistence = _clip(_mean(persists), 0.0, 1.5)
    return recovery, persistence, current


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


def _normalize_capped(scores: Dict[str, float], budget: float) -> Dict[str, float]:
    positives = {k: max(0.0, _safe_float(v)) for k, v in scores.items()}
    if budget <= 0 or sum(positives.values()) <= 0:
        return {k: 0.0 for k in scores}
    weights = {k: budget * v / sum(positives.values()) for k, v in positives.items()}
    for _ in range(6):
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

    recovery: Dict[str, float] = {}
    persistence: Dict[str, float] = {}
    current_stress: Dict[str, float] = {}
    for s in available:
        if len(close[s].dropna()) < MIN_HISTORY:
            continue
        stress = _stress_series(close[s], high[s], low[s], volume[s])
        rec, per, cur = _half_life_proxy(stress)
        recovery[s] = rec
        persistence[s] = per
        current_stress[s] = cur

    if not recovery:
        return {s: 0.0 for s in symbols}

    risk_recovery = _mean(recovery.get(s, 0.0) for s in RISK_ASSETS if s in recovery)
    def_recovery = _mean(recovery.get(s, 0.0) for s in DEFENSIVE_ASSETS if s in recovery)
    risk_persistence = _mean(persistence.get(s, 0.0) for s in RISK_ASSETS if s in persistence)
    broad_persistence = _mean(persistence.values())
    broad_stress = _mean(current_stress.values())

    recovery_breadth = sum(1 for s in RISK_ASSETS if recovery.get(s, 0.0) > 0.20) / max(
        sum(1 for s in RISK_ASSETS if s in recovery), 1
    )
    risk_on_state = _clip(
        0.45 * risk_recovery + 0.25 * recovery_breadth + 0.20 * max(0.0, risk_recovery - def_recovery) - 0.30 * risk_persistence,
        -1.0,
        1.0,
    )
    risk_off_state = _clip(0.55 * broad_persistence + 0.35 * broad_stress - 0.30 * risk_recovery, 0.0, 1.25)

    risk_budget = _clip(0.52 + 0.42 * risk_on_state - 0.35 * risk_off_state, 0.18, 0.78)
    defensive_budget = _clip(0.30 + 0.42 * risk_off_state - 0.20 * max(risk_on_state, 0.0), 0.18, 0.72)
    gross = _clip(risk_budget + defensive_budget, MIN_GROSS, 1.0)
    scale = gross / max(risk_budget + defensive_budget, 1e-12)
    risk_budget *= scale
    defensive_budget *= scale

    risk_scores: Dict[str, float] = {}
    for s in RISK_ASSETS:
        if s not in available:
            continue
        trend = _clip(_ret(close, s, TREND_WINDOW) / 0.10, -1.0, 1.0)
        realized_vol = _vol(close, s, VOL_WINDOW)
        risk_scores[s] = max(
            0.05,
            1.0 + 0.75 * recovery.get(s, 0.0) + 0.25 * trend - 0.70 * persistence.get(s, 0.0) - 0.20 * realized_vol,
        )

    defensive_scores: Dict[str, float] = {}
    for s in DEFENSIVE_ASSETS:
        if s not in available:
            continue
        trend = _clip(_ret(close, s, TREND_WINDOW) / 0.08, -1.0, 1.0)
        defensive_scores[s] = max(
            0.05,
            1.0 + 0.45 * persistence.get(s, 0.0) + 0.25 * trend - 0.25 * current_stress.get(s, 0.0),
        )

    weights = {s: 0.0 for s in symbols}
    for k, v in _normalize_capped(risk_scores, risk_budget).items():
        weights[k] = weights.get(k, 0.0) + v
    for k, v in _normalize_capped(defensive_scores, defensive_budget).items():
        weights[k] = weights.get(k, 0.0) + v
    return {s: _safe_float(weights.get(s, 0.0)) for s in symbols}
