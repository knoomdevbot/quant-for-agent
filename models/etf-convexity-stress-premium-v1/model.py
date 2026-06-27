"""AR-050 ETF convexity stress-premium allocator.

QFA contract: expose generate_signals(context) -> dict[str, float].

The model uses only Alpaca OHLCV history supplied by qfa.  It deliberately
avoids the AR-037 carry/defensive allocation mechanism: the regime variable is
built from realized-volatility acceleration, downside-volatility asymmetry,
range expansion, and equity stress breadth.  The allocator is long-only and
keeps a capped convexity sleeve (VIXY) only when stress is rising; otherwise it
holds a diversified low-beta ETF mix with a cash/SHY ballast.
"""

from __future__ import annotations

import math
from typing import Dict, Iterable

import pandas as pd

UNIVERSE = ("SPY", "QQQ", "IWM", "TLT", "IEF", "SHY", "GLD", "XLU", "VIXY")
RISK_ASSETS = ("SPY", "QQQ", "IWM")
DEFENSIVE_ASSETS = ("TLT", "IEF", "SHY", "GLD", "XLU")
CONVEXITY_ASSETS = ("VIXY",)

MIN_HISTORY = 150
FAST_VOL_WINDOW = 10
MID_VOL_WINDOW = 21
SLOW_VOL_WINDOW = 63
RANGE_WINDOW = 63
DRAWDOWN_WINDOW = 42
MAX_SINGLE_WEIGHT = 0.34
MAX_VIXY_WEIGHT = 0.09
MIN_GROSS = 0.72


def _safe_float(value, default: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return default
    return out if math.isfinite(out) else default


def _clip(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _series(frame: pd.DataFrame, symbol: str) -> pd.Series:
    if symbol not in frame.columns:
        return pd.Series(dtype=float)
    return frame[symbol].dropna()


def _ret(close: pd.DataFrame, symbol: str, window: int) -> float:
    s = _series(close, symbol)
    if len(s) <= window or s.iloc[-window - 1] <= 0:
        return 0.0
    return _safe_float(s.iloc[-1] / s.iloc[-window - 1] - 1.0)


def _vol(close: pd.DataFrame, symbol: str, window: int) -> float:
    s = _series(close, symbol)
    if len(s) <= window + 2:
        return 0.0
    r = s.pct_change().dropna().tail(window)
    if len(r) < max(5, window // 2):
        return 0.0
    return _safe_float(r.std(ddof=1) * math.sqrt(252.0))


def _downside_share(close: pd.DataFrame, symbol: str, window: int) -> float:
    s = _series(close, symbol)
    if len(s) <= window + 2:
        return 0.5
    r = s.pct_change().dropna().tail(window)
    if len(r) < max(10, window // 2):
        return 0.5
    dn = r[r < 0]
    up = r[r > 0]
    down_var = _safe_float((dn * dn).mean(), 0.0)
    up_var = _safe_float((up * up).mean(), 0.0)
    denom = down_var + up_var
    return _clip(down_var / denom if denom > 1e-12 else 0.5, 0.0, 1.0)


def _drawdown(close: pd.DataFrame, symbol: str, window: int) -> float:
    s = _series(close, symbol).tail(window)
    if len(s) < 2:
        return 0.0
    return _safe_float((s.iloc[-1] / s.cummax().max()) - 1.0)


def _range_z(high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame, symbol: str) -> float:
    if symbol not in high.columns or symbol not in low.columns or symbol not in close.columns:
        return 0.0
    h = high[symbol].dropna()
    low_series = low[symbol].reindex(h.index).ffill()
    c = close[symbol].reindex(h.index).ffill()
    rng = ((h - low_series) / c.shift(1)).replace([math.inf, -math.inf], pd.NA).dropna()
    if len(rng) < RANGE_WINDOW + 5:
        return 0.0
    hist = rng.iloc[-RANGE_WINDOW - 1 : -1].dropna()
    sd = _safe_float(hist.std(ddof=1))
    if sd <= 1e-12:
        return 0.0
    return _clip((_safe_float(rng.iloc[-1]) - _safe_float(hist.mean())) / sd, -3.0, 3.0)


def _basket_avg(values: Iterable[float]) -> float:
    vals = [v for v in values if math.isfinite(v)]
    return sum(vals) / len(vals) if vals else 0.0


def _stress(close: pd.DataFrame, high: pd.DataFrame, low: pd.DataFrame) -> tuple[float, Dict[str, float]]:
    components: Dict[str, float] = {}
    for s in RISK_ASSETS:
        if s not in close.columns:
            continue
        fast = _vol(close, s, FAST_VOL_WINDOW)
        mid = _vol(close, s, MID_VOL_WINDOW)
        slow = _vol(close, s, SLOW_VOL_WINDOW)
        vol_accel = _clip((fast - slow) / max(slow, 0.08), -1.0, 2.0)
        vol_convexity = _clip((fast - mid) / max(mid, 0.08), -1.0, 2.0)
        downside = _clip((_downside_share(close, s, SLOW_VOL_WINDOW) - 0.50) / 0.25, 0.0, 1.0)
        dd = _clip(abs(min(0.0, _drawdown(close, s, DRAWDOWN_WINDOW))) / 0.14, 0.0, 1.0)
        range_pressure = _clip(max(0.0, _range_z(high, low, close, s)) / 2.5, 0.0, 1.0)
        recent_loss = _clip(max(0.0, -_ret(close, s, 5)) / 0.045, 0.0, 1.0)
        raw = (
            0.30 * _clip(vol_accel / 1.2, 0.0, 1.0)
            + 0.18 * _clip(vol_convexity / 1.0, 0.0, 1.0)
            + 0.18 * downside
            + 0.16 * dd
            + 0.10 * range_pressure
            + 0.08 * recent_loss
        )
        components[s] = _clip(raw, 0.0, 1.0)
    breadth = sum(1 for v in components.values() if v > 0.45) / max(len(components), 1)
    stress = _clip(0.78 * _basket_avg(components.values()) + 0.22 * breadth, 0.0, 1.0)
    return stress, components


def _normalize(scores: Dict[str, float], budget: float, cap: float = MAX_SINGLE_WEIGHT) -> Dict[str, float]:
    positives = {k: max(0.0, _safe_float(v)) for k, v in scores.items()}
    total = sum(positives.values())
    if budget <= 0 or total <= 1e-12:
        return {k: 0.0 for k in scores}
    weights = {k: budget * v / total for k, v in positives.items()}
    for _ in range(6):
        excess = sum(max(0.0, w - cap) for w in weights.values())
        if excess <= 1e-12:
            break
        capped = {k for k, w in weights.items() if w >= cap}
        for k in capped:
            weights[k] = min(weights[k], cap)
        free = {k: positives[k] for k in weights if k not in capped and positives[k] > 0}
        free_total = sum(free.values())
        if free_total <= 1e-12:
            break
        for k, v in free.items():
            weights[k] += excess * v / free_total
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

    if len(close) < MIN_HISTORY:
        return {s: 0.0 for s in symbols}
    available = [s for s in symbols if s in UNIVERSE and s in close.columns]
    if len(available) < 6:
        return {s: 0.0 for s in symbols}

    stress, risk_components = _stress(close, high, low)
    gross_target = _clip(0.96 - 0.20 * max(0.0, stress - 0.65), MIN_GROSS, 1.0)
    convexity_budget = _clip((stress - 0.50) / 0.50, 0.0, 1.0) * MAX_VIXY_WEIGHT
    defensive_budget = _clip(0.30 + 0.48 * stress, 0.25, 0.78)
    risk_budget = max(0.0, gross_target - defensive_budget - convexity_budget)

    risk_scores: Dict[str, float] = {}
    for s in RISK_ASSETS:
        if s not in available:
            continue
        # Allocate risk capital to ETFs least implicated in the volatility shock,
        # with only a mild medium-horizon trend term to avoid pure momentum/carry.
        risk_scores[s] = max(0.05, 1.0 - 0.85 * risk_components.get(s, stress) + 0.15 * _clip(_ret(close, s, 21) / 0.06, -1.0, 1.0))

    defensive_scores: Dict[str, float] = {}
    for s in DEFENSIVE_ASSETS:
        if s not in available:
            continue
        short_vol = _vol(close, s, MID_VOL_WINDOW)
        range_pressure = max(0.0, _range_z(high, low, close, s))
        ballast = 1.0 - 0.50 * _clip(short_vol / 0.22, 0.0, 1.0) - 0.20 * _clip(range_pressure / 2.5, 0.0, 1.0)
        stress_fit = 0.20 if s in ("SHY", "IEF") else 0.12
        defensive_scores[s] = max(0.05, ballast + stress_fit * stress)

    weights = {s: 0.0 for s in symbols}
    for k, v in _normalize(risk_scores, risk_budget).items():
        weights[k] = weights.get(k, 0.0) + v
    for k, v in _normalize(defensive_scores, defensive_budget).items():
        weights[k] = weights.get(k, 0.0) + v

    if "VIXY" in available and convexity_budget > 0:
        vixy_penalty = _clip(_vol(close, "VIXY", MID_VOL_WINDOW) / 1.40, 0.0, 1.0)
        vixy_weight = convexity_budget * (1.0 - 0.35 * vixy_penalty)
        weights["VIXY"] = min(MAX_VIXY_WEIGHT, max(0.0, vixy_weight))

    gross = sum(max(0.0, _safe_float(v)) for v in weights.values())
    if gross > 1.0:
        weights = {k: v / gross for k, v in weights.items()}
    return {s: _safe_float(weights.get(s, 0.0)) for s in symbols}
