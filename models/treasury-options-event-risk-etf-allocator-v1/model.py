"""AR-100 treasury options-implied/event-risk ETF allocator.

QFA contract: expose generate_signals(context) -> dict[str, float].
Uses only OHLCV bars supplied by qfa/Alpaca. No option feed is assumed; event-risk
is proxied by realized range/volume shocks in liquid rate-sensitive ETFs.
Long-only, gross <= 1, no leverage.
"""

from __future__ import annotations

import math
from datetime import date
from typing import Dict, Iterable

import pandas as pd

UNIVERSE = (
    "BIL", "SHV", "SHY", "IEI", "IEF", "TLH", "TLT", "AGG", "LQD", "HYG", "EMB",
    "GLD", "SLV", "DBC", "USO", "SPY", "QQQ", "IWM", "DIA", "XLU", "XLP", "XLV",
    "XLE", "XLF", "XLK", "XLI", "VIXY",
)
CASH_LIKE = ("BIL", "SHV", "SHY")
DURATION = ("IEI", "IEF", "TLH", "TLT")
CREDIT = ("LQD", "HYG", "EMB")
REAL_ASSETS = ("GLD", "SLV", "DBC", "USO", "XLE")
EQUITY = ("SPY", "QQQ", "IWM", "DIA", "XLK", "XLF", "XLI")
DEFENSIVE = ("XLU", "XLP", "XLV", "GLD", "IEF", "SHY")
VOL_PROXY = ("VIXY",)

MIN_HISTORY = 150
FAST = 5
MED = 21
SLOW = 63
LONG = 126
MAX_SINGLE = 0.35


def _safe(x: float, default: float = 0.0) -> float:
    try:
        y = float(x)
    except Exception:
        return default
    return y if math.isfinite(y) else default


def _series(frame: pd.DataFrame, sym: str) -> pd.Series:
    if sym not in frame.columns:
        return pd.Series(dtype=float)
    return frame[sym].dropna()


def _ret(close: pd.DataFrame, sym: str, n: int) -> float:
    s = _series(close, sym)
    if len(s) <= n or s.iloc[-n - 1] <= 0:
        return 0.0
    return _safe(s.iloc[-1] / s.iloc[-n - 1] - 1.0)


def _vol(close: pd.DataFrame, sym: str, n: int = SLOW) -> float:
    s = _series(close, sym)
    if len(s) <= n:
        return 0.0
    r = s.pct_change().dropna().tail(n)
    return _safe(r.std() * math.sqrt(252.0))


def _range_z(high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame, sym: str, n: int = SLOW) -> float:
    if sym not in high.columns or sym not in low.columns or sym not in close.columns:
        return 0.0
    high_series = high[sym].dropna()
    low_series = low[sym].dropna()
    close_series = close[sym].dropna()
    df = pd.concat([high_series, low_series, close_series.shift(1)], axis=1).dropna().tail(n + 1)
    if len(df) < 30:
        return 0.0
    tr = (df.iloc[:, 0] - df.iloc[:, 1]).abs() / df.iloc[:, 2].replace(0, pd.NA)
    tr = tr.dropna()
    if len(tr) < 30 or tr.iloc[:-1].std() <= 1e-12:
        return 0.0
    return max(-4.0, min(4.0, _safe((tr.iloc[-1] - tr.iloc[:-1].mean()) / tr.iloc[:-1].std())))


def _vol_z(volume: pd.DataFrame, sym: str, n: int = SLOW) -> float:
    s = _series(volume, sym).tail(n + 1)
    if len(s) < 30:
        return 0.0
    lv = (s + 1.0).map(math.log)
    sd = lv.iloc[:-1].std()
    if sd <= 1e-12:
        return 0.0
    return max(-4.0, min(4.0, _safe((lv.iloc[-1] - lv.iloc[:-1].mean()) / sd)))


def _z(scores: Dict[str, float]) -> Dict[str, float]:
    vals = [v for v in scores.values() if math.isfinite(v)]
    if len(vals) < 2:
        return {k: 0.0 for k in scores}
    mean = sum(vals) / len(vals)
    sd = math.sqrt(sum((v - mean) ** 2 for v in vals) / max(len(vals) - 1, 1))
    if sd <= 1e-12:
        return {k: 0.0 for k in scores}
    return {k: max(-3.0, min(3.0, (v - mean) / sd)) for k, v in scores.items()}


def _calendar_gate(day: date) -> float:
    # Ex-ante approximation to macro-event clustering: CPI/PPI mid-month, payrolls
    # first Friday area, and FOMC-heavy months around mid/late month.
    d = day.day
    fomc_month = day.month in {1, 3, 5, 6, 7, 9, 11, 12}
    near_inflation = 8 <= d <= 15
    near_payrolls = d <= 8
    near_fomc = fomc_month and (14 <= d <= 23)
    return 1.0 if (near_inflation or near_payrolls or near_fomc) else 0.35


def _add_budget(weights: dict[str, float], scores: Dict[str, float], budget: float) -> None:
    scores = {s: max(0.0, v) for s, v in scores.items() if s in weights}
    if budget <= 0 or not scores:
        return
    total = sum(scores.values())
    if total <= 1e-12:
        for s in scores:
            weights[s] += budget / len(scores)
    else:
        for s, v in scores.items():
            weights[s] += budget * v / total


def _score_group(close: pd.DataFrame, symbols: Iterable[str], risk_penalty: float = 0.25) -> Dict[str, float]:
    raw = {}
    for s in symbols:
        if s in close.columns:
            raw[s] = 0.35 * _ret(close, s, FAST) + 0.45 * _ret(close, s, MED) + 0.25 * _ret(close, s, SLOW) - risk_penalty * _vol(close, s)
    return {s: 1.0 + z for s, z in _z(raw).items()}


def generate_signals(context) -> dict[str, float]:
    output = list(context.symbols)
    if context.prices is None or context.prices.empty:
        return {s: 0.0 for s in output}

    prices = context.prices.copy()
    prices["timestamp"] = pd.to_datetime(prices["timestamp"], utc=True)
    close = prices.pivot(index="timestamp", columns="symbol", values="close").sort_index().ffill()
    high = prices.pivot(index="timestamp", columns="symbol", values="high").sort_index().ffill()
    low = prices.pivot(index="timestamp", columns="symbol", values="low").sort_index().ffill()
    volume = prices.pivot(index="timestamp", columns="symbol", values="volume").sort_index().ffill()
    if len(close) < MIN_HISTORY:
        return {s: 0.0 for s in output}

    available = [s for s in output if s in UNIVERSE and s in close.columns]
    if len(available) < 10:
        return {s: 0.0 for s in output}

    as_of = pd.Timestamp(getattr(context, "as_of", close.index[-1])).date()
    gate = _calendar_gate(as_of)

    rate_risk = sum(_range_z(high, low, close, s) for s in ("IEF", "TLT", "LQD") if s in close.columns) / max(1, sum(s in close.columns for s in ("IEF", "TLT", "LQD")))
    equity_risk = sum(_range_z(high, low, close, s) for s in ("SPY", "QQQ", "IWM") if s in close.columns) / max(1, sum(s in close.columns for s in ("SPY", "QQQ", "IWM")))
    volume_risk = sum(_vol_z(volume, s) for s in ("TLT", "IEF", "LQD", "SPY", "GLD") if s in volume.columns) / max(1, sum(s in volume.columns for s in ("TLT", "IEF", "LQD", "SPY", "GLD")))
    realized_event_risk = max(0.0, min(1.0, gate * (0.35 + 0.18 * rate_risk + 0.14 * equity_risk + 0.10 * volume_risk)))

    duration_trend = 0.55 * _ret(close, "IEF", MED) + 0.45 * _ret(close, "TLT", MED)
    equity_trend = 0.50 * _ret(close, "SPY", MED) + 0.50 * _ret(close, "QQQ", MED)
    gold_trend = _ret(close, "GLD", MED)
    credit_stress = _ret(close, "LQD", MED) - _ret(close, "HYG", MED)
    risk_off = max(0.0, min(1.0, realized_event_risk + max(0.0, -equity_trend) / 0.08 + max(0.0, credit_stress) / 0.05))
    duration_favored = max(0.0, min(1.0, 0.45 + duration_trend / 0.08 - max(0.0, _ret(close, "DBC", MED)) / 0.12))
    inflation_favored = max(0.0, min(1.0, 0.25 + gold_trend / 0.07 + _ret(close, "DBC", MED) / 0.10 - duration_trend / 0.10))

    weights = {s: 0.0 for s in output}
    cash_budget = 0.16 + 0.30 * (1.0 - realized_event_risk)
    duration_budget = (0.16 + 0.34 * risk_off) * duration_favored
    real_asset_budget = (0.10 + 0.28 * realized_event_risk) * inflation_favored
    defensive_budget = 0.08 + 0.22 * risk_off
    credit_budget = max(0.02, 0.16 * (1.0 - risk_off))
    equity_budget = max(0.03, 1.0 - cash_budget - duration_budget - real_asset_budget - defensive_budget - credit_budget)
    if "VIXY" in available and realized_event_risk > 0.65 and equity_trend < 0:
        weights["VIXY"] = min(0.06, 0.02 + 0.04 * risk_off)
        equity_budget *= 0.85

    _add_budget(weights, _score_group(close, CASH_LIKE, 0.02), cash_budget)
    _add_budget(weights, _score_group(close, DURATION, 0.18), duration_budget)
    _add_budget(weights, _score_group(close, REAL_ASSETS, 0.28), real_asset_budget)
    _add_budget(weights, _score_group(close, DEFENSIVE, 0.20), defensive_budget)
    _add_budget(weights, _score_group(close, CREDIT, 0.22), credit_budget)
    _add_budget(weights, _score_group(close, EQUITY, 0.38), equity_budget)

    capped = {s: max(0.0, min(MAX_SINGLE, _safe(weights.get(s, 0.0)))) for s in output}
    gross = sum(capped.values())
    if gross <= 1e-12:
        return {s: 0.0 for s in output}
    return {s: capped[s] / gross for s in output}
