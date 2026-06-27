"""AR-088 ETF realized-volatility asymmetry defensive allocator.

QFA contract: generate_signals(context) -> dict[str, float].
Uses only qfa/Alpaca OHLCV bars supplied in context. No orders, no daemon, no CSV.
"""

from __future__ import annotations

import math
from typing import Mapping

import pandas as pd

UNIVERSE = ("SPY", "QQQ", "TLT", "IEF", "GLD", "XLU", "XLP", "XLV", "HYG", "LQD", "SHY")
RISK_ASSETS = ("SPY", "QQQ", "HYG", "LQD", "XLV")
DEFENSIVE_ASSETS = ("IEF", "TLT", "GLD", "XLU", "XLP", "XLV", "SHY")
EQUITY_STRESS = ("SPY", "QQQ", "XLU", "XLP", "XLV")
MIN_HISTORY = 155
FAST = 21
MED = 63
SLOW = 126
MAX_SINGLE = 0.35
EPS = 1e-12


def _finite(x: float, default: float = 0.0) -> float:
    try:
        y = float(x)
    except Exception:
        return default
    return y if math.isfinite(y) else default


def _clip(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, _finite(x)))


def _series(close: pd.DataFrame, symbol: str) -> pd.Series:
    if symbol not in close.columns:
        return pd.Series(dtype=float)
    return close[symbol].dropna()


def _ret(close: pd.DataFrame, symbol: str, n: int) -> float:
    s = _series(close, symbol)
    if len(s) <= n or s.iloc[-n - 1] <= 0:
        return 0.0
    return _finite(s.iloc[-1] / s.iloc[-n - 1] - 1.0)


def _drawdown(close: pd.DataFrame, symbol: str, n: int = MED) -> float:
    s = _series(close, symbol).tail(n)
    if len(s) < 2:
        return 0.0
    return _finite((s.iloc[-1] / s.cummax().iloc[-1]) - 1.0)


def _vol(close: pd.DataFrame, symbol: str, n: int = MED) -> float:
    r = _series(close, symbol).pct_change().dropna().tail(n)
    if len(r) < max(10, n // 3):
        return 0.0
    return _finite(r.std(ddof=1) * math.sqrt(252.0))


def _semivol_ratio_history(close: pd.DataFrame, symbol: str, window: int = MED, zwin: int = SLOW) -> pd.Series:
    """Rolling downside/upside semivolatility ratio; >1 means downside-vol dominance."""
    r = _series(close, symbol).pct_change().dropna()
    if len(r) < window + 5:
        return pd.Series(dtype=float)
    downside = r.where(r < 0.0, 0.0).rolling(window).std(ddof=1)
    upside = r.where(r > 0.0, 0.0).rolling(window).std(ddof=1)
    ratio = downside / (upside + EPS)
    return ratio.dropna().tail(zwin)


def _ratio_z(close: pd.DataFrame, symbol: str, window: int = MED, zwin: int = SLOW) -> float:
    hist = _semivol_ratio_history(close, symbol, window=window, zwin=zwin)
    if len(hist) < max(20, window // 2):
        return 0.0
    sd = hist.std(ddof=1)
    if not math.isfinite(float(sd)) or sd <= EPS:
        return 0.0
    return _clip((hist.iloc[-1] - hist.mean()) / sd, -3.0, 3.0)


def _cross_z(values: Mapping[str, float]) -> dict[str, float]:
    xs = [v for v in values.values() if math.isfinite(v)]
    if len(xs) < 2:
        return {k: 0.0 for k in values}
    mean = sum(xs) / len(xs)
    sd = math.sqrt(sum((v - mean) ** 2 for v in xs) / max(len(xs) - 1, 1))
    if sd <= EPS:
        return {k: 0.0 for k in values}
    return {k: _clip((v - mean) / sd, -3.0, 3.0) for k, v in values.items()}


def _add_scaled(weights: dict[str, float], scores: Mapping[str, float], budget: float) -> None:
    if budget <= 0:
        return
    clean = {k: max(0.0, _finite(v)) for k, v in scores.items() if k in weights}
    total = sum(clean.values())
    if not clean:
        return
    if total <= EPS:
        each = budget / len(clean)
        for k in clean:
            weights[k] += each
    else:
        for k, v in clean.items():
            weights[k] += budget * v / total


def generate_signals(context) -> dict[str, float]:
    symbols = list(context.symbols)
    if context.prices is None or context.prices.empty:
        return {s: 0.0 for s in symbols}

    prices = context.prices.copy()
    prices["timestamp"] = pd.to_datetime(prices["timestamp"], utc=True)
    close = prices.pivot(index="timestamp", columns="symbol", values="close").sort_index().ffill()
    if len(close) < MIN_HISTORY:
        return {s: 0.0 for s in symbols}

    available = [s for s in symbols if s in UNIVERSE and s in close.columns]
    if len(available) < 7 or "SHY" not in available:
        return {s: 0.0 for s in symbols}

    ratio_z = {s: _ratio_z(close, s, MED, SLOW) for s in available}
    equity_down_z = sum(ratio_z.get(s, 0.0) for s in EQUITY_STRESS if s in available) / max(
        1, sum(1 for s in EQUITY_STRESS if s in available)
    )
    credit_down_z = (ratio_z.get("HYG", 0.0) + ratio_z.get("LQD", 0.0)) / max(
        1, int("HYG" in available) + int("LQD" in available)
    )
    spy_vol_trend = (_vol(close, "SPY", FAST) - _vol(close, "SPY", SLOW)) / max(_vol(close, "SPY", SLOW), 0.05)
    credit_confirm = _clip((-_ret(close, "HYG", MED) + _ret(close, "IEF", MED)) / 0.08, 0.0, 1.0)
    drawdown_confirm = _clip((-_drawdown(close, "SPY", MED)) / 0.12, 0.0, 1.0)

    stress = _clip(
        0.28 * equity_down_z
        + 0.22 * credit_down_z
        + 0.18 * spy_vol_trend
        + 0.18 * credit_confirm
        + 0.14 * drawdown_confirm,
        0.0,
        1.0,
    )
    upside_regime = _clip((-0.45 * equity_down_z - 0.20 * credit_down_z + 0.35 * _ret(close, "SPY", MED) / 0.10), 0.0, 1.0)

    weights = {s: 0.0 for s in symbols}

    risk_budget = _clip(0.42 + 0.25 * upside_regime - 0.52 * stress, 0.08, 0.62)
    duration_budget = _clip(0.18 + 0.22 * stress - 0.08 * max(0.0, _ret(close, "TLT", MED) < -0.04), 0.08, 0.42)
    gold_budget = _clip(0.10 + 0.10 * stress + 0.08 * max(0.0, _ret(close, "GLD", MED)), 0.04, 0.24)
    sector_def_budget = _clip(0.16 + 0.10 * stress, 0.10, 0.28)
    shy_budget = max(0.06, 1.0 - risk_budget - duration_budget - gold_budget - sector_def_budget)
    scale = 1.0 / (risk_budget + duration_budget + gold_budget + sector_def_budget + shy_budget)
    risk_budget *= scale
    duration_budget *= scale
    gold_budget *= scale
    sector_def_budget *= scale
    shy_budget *= scale

    # Risk sleeve favors upside-vol dominance and trend, but penalizes downside semivolatility asymmetry.
    risk_raw = {}
    for s in RISK_ASSETS:
        if s in available:
            risk_raw[s] = 0.75 * _ret(close, s, MED) + 0.35 * _ret(close, s, FAST) - 0.09 * ratio_z.get(s, 0.0) - 0.45 * stress
    risk_scores = {s: 1.0 + z for s, z in _cross_z(risk_raw).items()}
    _add_scaled(weights, risk_scores, risk_budget)

    dur_raw = {}
    for s in ("IEF", "TLT"):
        if s in available:
            dur_raw[s] = 0.45 * stress + 0.55 * _ret(close, s, MED) + 0.20 * _ret(close, s, SLOW) - 0.25 * _vol(close, s, MED)
    _add_scaled(weights, {s: 1.0 + z for s, z in _cross_z(dur_raw).items()}, duration_budget)

    if "GLD" in weights:
        weights["GLD"] += gold_budget

    sector_raw = {}
    for s in ("XLU", "XLP", "XLV"):
        if s in available:
            sector_raw[s] = 0.35 * stress - 0.12 * ratio_z.get(s, 0.0) + 0.65 * _ret(close, s, MED) - 0.20 * _vol(close, s, MED)
    _add_scaled(weights, {s: 1.0 + z for s, z in _cross_z(sector_raw).items()}, sector_def_budget)

    weights["SHY"] += shy_budget

    capped = {s: _clip(weights.get(s, 0.0), 0.0, MAX_SINGLE) for s in symbols}
    gross = sum(capped.values())
    if gross <= EPS:
        return {s: 0.0 for s in symbols}
    return {s: round(capped[s] / gross, 10) for s in symbols}
