"""AR-040 yield/credit stress ETF allocation.

Rule-based qfa model using only daily OHLCV bars supplied by qfa. The signal is
macro-stress oriented: duration and gold strength, defensive-vs-cyclical sector
spreads, credit proxy HYG-vs-LQD weakness, and equity breadth determine a
risk-aversion score. Allocations shift between broad/cyclical equity ETFs and
Treasury/gold/defensive sector ETFs; it is intentionally not a pure
cross-sectional ETF momentum ranker.
"""

from __future__ import annotations

import math
from typing import Dict, Iterable

import pandas as pd

UNIVERSE = (
    "SPY", "QQQ", "IWM", "TLT", "IEF", "GLD", "HYG", "LQD",
    "XLP", "XLU", "XLV", "XLY", "XLI", "XLK", "XLF",
)
RISK_ON = ("SPY", "QQQ", "IWM", "XLY", "XLI", "XLK", "XLF", "HYG")
RISK_OFF = ("TLT", "IEF", "GLD", "XLP", "XLU", "XLV", "LQD")
DEFENSIVE_SECTORS = ("XLP", "XLU", "XLV")
CYCLICAL_SECTORS = ("XLY", "XLI", "XLK", "XLF")

STRESS_WINDOW = 60
SLOW_WINDOW = 126
SHORT_WINDOW = 20
VOL_WINDOW = 60
MIN_HISTORY = 150
MAX_SINGLE_WEIGHT = 0.28
MIN_GROSS_EXPOSURE = 0.72


def _safe_float(value, default: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return default
    return out if math.isfinite(out) else default


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
    if len(s) <= window:
        return 0.0
    r = s.pct_change().dropna().tail(window)
    return _safe_float(r.std() * math.sqrt(252.0))


def _basket_ret(close: pd.DataFrame, symbols: Iterable[str], window: int) -> float:
    vals = [_ret(close, s, window) for s in symbols if s in close.columns]
    return sum(vals) / len(vals) if vals else 0.0


def _z_unit(x: float, scale: float) -> float:
    if scale <= 0:
        return 0.0
    return max(-1.0, min(1.0, x / scale))


def _normalize_scores(scores: Dict[str, float], budget: float) -> Dict[str, float]:
    positives = {k: max(0.0, v) for k, v in scores.items()}
    total = sum(positives.values())
    if budget <= 0 or total <= 0:
        return {k: 0.0 for k in scores}
    return {k: budget * v / total for k, v in positives.items()}


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
    if len(available) < 8:
        return {s: 0.0 for s in symbols}

    # Macro-stress proxies: higher values mean stronger demand for havens.
    duration_strength = 0.55 * _ret(close, "TLT", STRESS_WINDOW) + 0.45 * _ret(close, "IEF", STRESS_WINDOW)
    gold_strength = _ret(close, "GLD", STRESS_WINDOW)
    defensive_spread = _basket_ret(close, DEFENSIVE_SECTORS, STRESS_WINDOW) - _basket_ret(close, CYCLICAL_SECTORS, STRESS_WINDOW)
    credit_stress = _ret(close, "LQD", STRESS_WINDOW) - _ret(close, "HYG", STRESS_WINDOW)
    equity_breadth = sum(1 for s in ("SPY", "QQQ", "IWM", "XLY", "XLI", "XLK", "XLF") if _ret(close, s, SHORT_WINDOW) > 0)
    breadth_stress = 1.0 - equity_breadth / 7.0
    spy_vol = _vol(close, "SPY", SHORT_WINDOW) or _vol(close, "SPY", VOL_WINDOW)
    vol_stress = max(0.0, min(1.0, (spy_vol - 0.14) / 0.26))

    stress_raw = (
        0.25 * _z_unit(duration_strength, 0.08)
        + 0.20 * _z_unit(gold_strength, 0.07)
        + 0.25 * _z_unit(defensive_spread, 0.06)
        + 0.15 * _z_unit(credit_stress, 0.04)
        + 0.10 * breadth_stress
        + 0.05 * vol_stress
    )
    stress = max(0.0, min(1.0, 0.50 + stress_raw))

    # Budgets retain exposure in all regimes but reduce gross when stress is extreme.
    risk_off_budget = 0.25 + 0.55 * stress
    risk_on_budget = 0.72 - 0.47 * stress
    gross_target = max(MIN_GROSS_EXPOSURE, min(1.0, risk_off_budget + risk_on_budget))
    scale = gross_target / max(risk_off_budget + risk_on_budget, 1e-12)
    risk_off_budget *= scale
    risk_on_budget *= scale

    # Risk-on sleeve favors resilient broad/cyclical ETFs but is mainly regime-budgeted.
    risk_on_scores: Dict[str, float] = {}
    for s in RISK_ON:
        if s in available:
            resilience = 1.0 + 0.6 * _z_unit(_ret(close, s, STRESS_WINDOW) - _vol(close, s, VOL_WINDOW) * 0.15, 0.10)
            risk_on_scores[s] = max(0.05, resilience)

    # Risk-off sleeve scores emphasize the distinct stress proxies rather than generic momentum.
    risk_off_scores: Dict[str, float] = {}
    for s in RISK_OFF:
        if s not in available:
            continue
        if s in ("TLT", "IEF"):
            score = 1.0 + 0.7 * _z_unit(duration_strength, 0.08) - 0.2 * _vol(close, s, VOL_WINDOW)
        elif s == "GLD":
            score = 1.0 + 0.8 * _z_unit(gold_strength, 0.07) - 0.1 * _vol(close, s, VOL_WINDOW)
        elif s == "LQD":
            score = 0.8 + 0.6 * _z_unit(credit_stress, 0.04) - 0.2 * _vol(close, s, VOL_WINDOW)
        else:
            score = 1.0 + 0.8 * _z_unit(defensive_spread, 0.06) - 0.15 * _vol(close, s, VOL_WINDOW)
        risk_off_scores[s] = max(0.05, score)

    weights = {s: 0.0 for s in symbols}
    for sleeve in (_normalize_scores(risk_on_scores, risk_on_budget), _normalize_scores(risk_off_scores, risk_off_budget)):
        for s, w in sleeve.items():
            if s in weights:
                weights[s] += w

    capped = {s: max(0.0, min(MAX_SINGLE_WEIGHT, _safe_float(weights.get(s, 0.0)))) for s in symbols}
    gross = sum(capped.values())
    if gross > 1.0:
        capped = {s: w / gross for s, w in capped.items()}
    return capped
