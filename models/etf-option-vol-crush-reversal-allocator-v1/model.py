"""AR-094 ETF option-implied-volatility crush reversal allocator.

QFA contract: generate_signals(context) -> dict[str, float].

Important data note: qfa/Alpaca supplies equity OHLCV bars only in this research
setup, not listed option chains or implied volatility. This model is therefore an
honest *realized-volatility/range crush proxy* for the hypothesized option-IV
shock/crush mechanism. It does not invent implied-volatility observations.
"""

from __future__ import annotations

import math
from typing import Mapping

import pandas as pd

UNIVERSE = ("SPY", "QQQ", "IWM", "TLT", "GLD", "HYG", "LQD", "XLU", "XLE", "SHY")
RISK_ASSETS = ("SPY", "QQQ", "IWM", "HYG", "XLE")
DEFENSIVE_ASSETS = ("TLT", "GLD", "LQD", "XLU", "SHY")
MIN_HISTORY = 150
EPS = 1e-12
MAX_SINGLE = 0.45


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


def _vol(close: pd.DataFrame, symbol: str, n: int) -> float:
    r = _series(close, symbol).pct_change().dropna().tail(n)
    if len(r) < max(5, n // 3):
        return 0.0
    return _finite(r.std(ddof=1) * math.sqrt(252.0))


def _drawdown(close: pd.DataFrame, symbol: str, n: int) -> float:
    s = _series(close, symbol).tail(n)
    if len(s) < 2:
        return 0.0
    return _finite(s.iloc[-1] / s.cummax().iloc[-1] - 1.0)


def _range_vol(prices: pd.DataFrame, n: int) -> pd.Series:
    px = prices.copy()
    rv = []
    for sym, g in px.groupby("symbol"):
        g = g.sort_values("timestamp").tail(n)
        if len(g) < max(5, n // 3):
            rv.append((sym, 0.0))
            continue
        close = g["close"].replace(0, pd.NA)
        hl = ((g["high"] - g["low"]) / close).astype(float).dropna()
        rv.append((sym, _finite(hl.mean() * math.sqrt(252.0))))
    return pd.Series(dict(rv), dtype=float)


def _cross_z(values: Mapping[str, float]) -> dict[str, float]:
    xs = [v for v in values.values() if math.isfinite(v)]
    if len(xs) < 2:
        return {k: 0.0 for k in values}
    mean = sum(xs) / len(xs)
    sd = math.sqrt(sum((x - mean) ** 2 for x in xs) / max(len(xs) - 1, 1))
    if sd <= EPS:
        return {k: 0.0 for k in values}
    return {k: _clip((v - mean) / sd, -3.0, 3.0) for k, v in values.items()}


def _add_scaled(weights: dict[str, float], scores: Mapping[str, float], budget: float) -> None:
    clean = {k: max(0.0, _finite(v)) for k, v in scores.items() if k in weights}
    if not clean or budget <= 0:
        return
    total = sum(clean.values())
    if total <= EPS:
        for k in clean:
            weights[k] += budget / len(clean)
    else:
        for k, v in clean.items():
            weights[k] += budget * v / total


def generate_signals(context) -> dict[str, float]:
    symbols = list(context.symbols)
    if context.prices is None or context.prices.empty:
        return {s: 0.0 for s in symbols}

    prices = context.prices.copy()
    prices["timestamp"] = pd.to_datetime(prices["timestamp"], utc=True)
    prices = prices[prices["symbol"].isin(UNIVERSE)].sort_values(["timestamp", "symbol"])
    close = prices.pivot(index="timestamp", columns="symbol", values="close").sort_index().ffill()
    available = [s for s in symbols if s in UNIVERSE and s in close.columns]
    if len(close) < MIN_HISTORY or len(available) < 8 or "SHY" not in available:
        return {s: 0.0 for s in symbols}

    rv5 = _range_vol(prices, 5)
    rv20 = _range_vol(prices, 20)
    rv63 = _range_vol(prices, 63)
    crush_by_symbol = {}
    shock_by_symbol = {}
    for s in available:
        fast, med, slow = _finite(rv5.get(s, 0.0)), _finite(rv20.get(s, 0.0)), _finite(rv63.get(s, 0.0))
        shock = _clip((med / max(slow, 0.04) - 1.0) / 0.75, 0.0, 1.5)
        crush = _clip((med - fast) / max(med, 0.04), 0.0, 1.0)
        shock_by_symbol[s] = shock
        crush_by_symbol[s] = crush

    risk_crush = sum(crush_by_symbol.get(s, 0.0) for s in ("SPY", "QQQ", "IWM", "HYG")) / 4.0
    risk_shock = sum(shock_by_symbol.get(s, 0.0) for s in ("SPY", "QQQ", "IWM", "HYG")) / 4.0
    spy_dd = -_drawdown(close, "SPY", 63)
    credit_mom = _ret(close, "HYG", 21) - _ret(close, "LQD", 21)
    trend_brake = _clip((-_ret(close, "SPY", 21) - 0.5 * _ret(close, "HYG", 21)) / 0.10, 0.0, 1.0)

    # Reversal is permitted only after an already-elevated realized/range vol state
    # starts to normalize. This is the explicit realized proxy for IV crush.
    crush_reversal = _clip(0.48 * risk_crush + 0.27 * risk_shock + 0.15 * max(0.0, credit_mom) / 0.03 - 0.35 * trend_brake, 0.0, 1.0)
    stress = _clip(0.45 * risk_shock + 0.30 * trend_brake + 0.25 * spy_dd / 0.12 - 0.25 * risk_crush, 0.0, 1.0)

    risk_budget = _clip(0.22 + 0.48 * crush_reversal - 0.35 * stress, 0.05, 0.70)
    duration_budget = _clip(0.16 + 0.23 * stress - 0.08 * max(0.0, _ret(close, "TLT", 63) < -0.04), 0.08, 0.38)
    gold_budget = _clip(0.10 + 0.12 * stress + 0.06 * max(0.0, _ret(close, "GLD", 63)), 0.05, 0.25)
    quality_budget = _clip(0.17 + 0.11 * stress - 0.08 * crush_reversal, 0.08, 0.30)
    cash_budget = max(0.03, 1.0 - risk_budget - duration_budget - gold_budget - quality_budget)
    scale = 1.0 / (risk_budget + duration_budget + gold_budget + quality_budget + cash_budget)
    risk_budget *= scale
    duration_budget *= scale
    gold_budget *= scale
    quality_budget *= scale
    cash_budget *= scale

    weights = {s: 0.0 for s in symbols}

    risk_raw = {}
    for s in RISK_ASSETS:
        if s in available:
            risk_raw[s] = 0.55 * crush_by_symbol.get(s, 0.0) + 0.35 * _ret(close, s, 21) + 0.25 * _ret(close, s, 63) - 0.18 * _vol(close, s, 20)
    _add_scaled(weights, {s: 1.0 + z for s, z in _cross_z(risk_raw).items()}, risk_budget)

    dur_raw = {s: 0.45 * stress + 0.40 * _ret(close, s, 63) - 0.15 * _vol(close, s, 20) for s in ("TLT", "LQD") if s in available}
    _add_scaled(weights, {s: 1.0 + z for s, z in _cross_z(dur_raw).items()}, duration_budget)
    if "GLD" in available:
        weights["GLD"] += gold_budget
    qual_raw = {s: 0.35 * stress + 0.45 * _ret(close, s, 63) - 0.20 * _vol(close, s, 20) for s in ("XLU", "LQD") if s in available}
    _add_scaled(weights, {s: 1.0 + z for s, z in _cross_z(qual_raw).items()}, quality_budget)
    if "SHY" in weights:
        weights["SHY"] += cash_budget

    capped = {s: _clip(weights.get(s, 0.0), 0.0, MAX_SINGLE) for s in symbols}
    gross = sum(capped.values())
    if gross <= EPS:
        return {s: 0.0 for s in symbols}
    return {s: round(capped[s] / gross, 10) for s in symbols}
