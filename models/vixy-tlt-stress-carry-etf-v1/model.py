"""AR-052 VIXY/TLT stress-carry ETF allocator.

QFA contract: expose generate_signals(context) -> dict[str, float].

Mechanism: use liquid ETFs only (VIXY, TLT, IEF, SHY, SPY).  The model is
not a price-momentum defensive rotation clone: it treats VIXY as a stress-state
sensor and small convexity sleeve, balances TLT/IEF duration carry/trend, and
falls back to SHY when VIXY carry decay and equity/duration signals are weak.
All inputs are OHLCV bars provided by qfa/Alpaca.
"""

from __future__ import annotations

import math
from typing import Dict

import pandas as pd

UNIVERSE = ("VIXY", "TLT", "IEF", "SHY", "SPY")
MIN_HISTORY = 145
MAX_VIXY_WEIGHT = 0.12
MAX_SINGLE_WEIGHT = 0.72


def _safe_float(value, default: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return default
    return out if math.isfinite(out) else default


def _clip(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _series(close: pd.DataFrame, symbol: str) -> pd.Series:
    if symbol not in close.columns:
        return pd.Series(dtype=float)
    return close[symbol].dropna()


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


def _drawdown(close: pd.DataFrame, symbol: str, window: int) -> float:
    s = _series(close, symbol).tail(window)
    if len(s) < 2:
        return 0.0
    peak = _safe_float(s.max())
    if peak <= 0:
        return 0.0
    return _safe_float(s.iloc[-1] / peak - 1.0)


def _range_z(prices: pd.DataFrame, symbol: str, window: int = 63) -> float:
    if prices.empty or symbol not in set(prices["symbol"]):
        return 0.0
    p = prices[prices["symbol"] == symbol].sort_values("timestamp").tail(window + 2)
    if len(p) < window // 2:
        return 0.0
    rng = ((p["high"].astype(float) - p["low"].astype(float)) / p["close"].astype(float).shift(1)).replace(
        [math.inf, -math.inf], pd.NA
    ).dropna()
    if len(rng) < 22:
        return 0.0
    hist = rng.iloc[:-1]
    sd = _safe_float(hist.std(ddof=1))
    if sd <= 1e-12:
        return 0.0
    return _clip((_safe_float(rng.iloc[-1]) - _safe_float(hist.mean())) / sd, -3.0, 3.0)


def _normalize(scores: Dict[str, float], budget: float, cap: float = MAX_SINGLE_WEIGHT) -> Dict[str, float]:
    positives = {k: max(0.0, _safe_float(v)) for k, v in scores.items()}
    total = sum(positives.values())
    if budget <= 0 or total <= 1e-12:
        return {k: 0.0 for k in scores}
    weights = {k: budget * v / total for k, v in positives.items()}
    for _ in range(8):
        capped = {k for k, w in weights.items() if w > cap}
        if not capped:
            break
        excess = sum(weights[k] - cap for k in capped)
        for k in capped:
            weights[k] = cap
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

    if len(close) < MIN_HISTORY:
        return {s: 0.0 for s in symbols}
    available = [s for s in symbols if s in UNIVERSE and s in close.columns]
    if len(available) < 4 or "SPY" not in available:
        return {s: 0.0 for s in symbols}

    spy_dd = abs(min(0.0, _drawdown(close, "SPY", 63)))
    spy_loss_10 = max(0.0, -_ret(close, "SPY", 10))
    spy_vol_fast = _vol(close, "SPY", 10)
    spy_vol_slow = max(_vol(close, "SPY", 63), 0.08)
    vixy_jump_5 = max(0.0, _ret(close, "VIXY", 5)) if "VIXY" in available else 0.0
    range_pressure = max(0.0, _range_z(prices, "SPY", 63))

    stress = _clip(
        0.30 * _clip(spy_dd / 0.12, 0.0, 1.0)
        + 0.22 * _clip(spy_loss_10 / 0.06, 0.0, 1.0)
        + 0.20 * _clip((spy_vol_fast / spy_vol_slow - 1.0) / 1.4, 0.0, 1.0)
        + 0.18 * _clip(vixy_jump_5 / 0.22, 0.0, 1.0)
        + 0.10 * _clip(range_pressure / 2.5, 0.0, 1.0),
        0.0,
        1.0,
    )

    # VIXY is held only as a small crash-convexity sleeve when stress is rising;
    # a 60-day decay/carry penalty avoids routine long VIXY exposure.
    vixy_decay = max(0.0, -_ret(close, "VIXY", 60)) if "VIXY" in available else 1.0
    vixy_vol = _vol(close, "VIXY", 21) if "VIXY" in available else 2.0
    convexity_budget = 0.0
    if "VIXY" in available:
        convexity_budget = MAX_VIXY_WEIGHT * _clip((stress - 0.42) / 0.38, 0.0, 1.0)
        convexity_budget *= 1.0 - 0.45 * _clip(vixy_decay / 0.45, 0.0, 1.0)
        convexity_budget *= 1.0 - 0.25 * _clip(vixy_vol / 1.60, 0.0, 1.0)

    tlt_trend = _ret(close, "TLT", 60) if "TLT" in available else 0.0
    ief_trend = _ret(close, "IEF", 60) if "IEF" in available else 0.0
    duration_trend = 0.65 * tlt_trend + 0.35 * ief_trend
    duration_budget = _clip(0.20 + 0.50 * stress + 1.40 * max(duration_trend, -0.03), 0.15, 0.78)
    duration_budget = min(duration_budget, 1.0 - convexity_budget)

    # Keep modest SPY exposure in benign regimes to pay for defensive carry drag;
    # otherwise use SHY as a true cash-like fallback.
    spy_budget = 0.0 if "SPY" not in available else _clip(0.30 * (1.0 - stress) + 0.35 * max(_ret(close, "SPY", 60), 0.0), 0.0, 0.45)
    if stress > 0.62:
        spy_budget *= 0.35
    if convexity_budget + duration_budget + spy_budget > 1.0:
        spy_budget = max(0.0, 1.0 - convexity_budget - duration_budget)
    shy_budget = max(0.0, 1.0 - convexity_budget - duration_budget - spy_budget)

    weights = {s: 0.0 for s in symbols}
    duration_scores: Dict[str, float] = {}
    if "TLT" in available:
        duration_scores["TLT"] = 0.65 + 2.5 * max(tlt_trend, -0.04) + 0.40 * stress - 0.35 * _clip(_vol(close, "TLT", 21) / 0.30, 0.0, 1.0)
    if "IEF" in available:
        duration_scores["IEF"] = 0.55 + 2.0 * max(ief_trend, -0.02) + 0.25 * stress - 0.25 * _clip(_vol(close, "IEF", 21) / 0.18, 0.0, 1.0)
    for k, v in _normalize(duration_scores, duration_budget).items():
        weights[k] = v
    if "VIXY" in available:
        weights["VIXY"] = convexity_budget
    if "SPY" in available:
        weights["SPY"] = spy_budget
    if "SHY" in available:
        weights["SHY"] = shy_budget

    gross = sum(max(0.0, _safe_float(v)) for v in weights.values())
    if gross > 1.0:
        weights = {k: v / gross for k, v in weights.items()}
    return {s: _safe_float(weights.get(s, 0.0)) for s in symbols}
