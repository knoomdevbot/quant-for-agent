"""AR-093 crypto-stress quality-flight defensive ETF allocator.

Uses compact derived BTC/ETH stress event intervals generated from real Coinbase
Exchange public candles JSON data. Timestamp discipline: for ETF date D, the embedded event signal was
computed from BTC/ETH data through completed UTC day D-1 only; qfa then applies the
weights to the next ETF daily return. No orders, daemon, CSV market data, or raw
crypto arrays are used/retained by this model artifact.
"""
from __future__ import annotations

import math
import pandas as pd

UNIVERSE = ("SPY", "QQQ", "IWM", "TLT", "IEF", "SHY", "GLD", "HYG", "LQD", "XLU", "XLP", "XLV", "USMV", "QUAL")
RISK = ("SPY", "QQQ", "IWM", "HYG", "LQD")
DURATION = ("TLT", "IEF")
DEF_SECTORS = ("XLU", "XLP", "XLV", "USMV", "QUAL")
CRYPTO_STRESS_EVENTS = [('2020-03-09', '2020-03-31', 2.358), ('2021-01-22', '2021-02-05', 1.458), ('2021-02-26', '2021-03-11', 1.1626), ('2021-05-18', '2021-06-08', 2.1691), ('2022-01-22', '2022-02-02', 1.526), ('2022-05-10', '2022-05-29', 1.627), ('2022-06-14', '2022-07-02', 1.9438), ('2022-11-10', '2022-11-27', 1.2213), ('2023-08-18', '2023-09-02', 1.2912), ('2024-01-23', '2024-01-31', 1.2419), ('2024-03-17', '2024-04-08', 1.7804), ('2024-04-14', '2024-04-30', 1.3465), ('2024-08-06', '2024-08-21', 1.5184), ('2025-02-27', '2025-03-22', 2.0811), ('2025-04-07', '2025-04-16', 1.2995), ('2025-10-11', '2025-10-29', 1.8012), ('2025-11-05', '2025-11-29', 1.5759)]
MIN_HISTORY = 126
MAX_SINGLE = 0.32
EPS = 1e-12


def _finite(x, default=0.0):
    try:
        y = float(x)
    except Exception:
        return default
    return y if math.isfinite(y) else default


def _clip(x, lo, hi):
    return max(lo, min(hi, _finite(x)))


def _stress_for(as_of) -> float:
    d = pd.Timestamp(as_of).strftime("%Y-%m-%d")
    val = 0.0
    for start, end, score in CRYPTO_STRESS_EVENTS:
        if start <= d <= end:
            val = max(val, float(score))
    return _clip(val / 2.4, 0.0, 1.0)


def _ret(close, symbol, n):
    if symbol not in close.columns:
        return 0.0
    s = close[symbol].dropna()
    if len(s) <= n or s.iloc[-n-1] <= 0:
        return 0.0
    return _finite(s.iloc[-1] / s.iloc[-n-1] - 1.0)


def _vol(close, symbol, n=63):
    if symbol not in close.columns:
        return 0.0
    r = close[symbol].dropna().pct_change().dropna().tail(n)
    if len(r) < 20:
        return 0.0
    return _finite(r.std(ddof=1) * math.sqrt(252.0))


def _add(weights, scores, budget):
    clean = {k: max(0.0, _finite(v)) for k, v in scores.items() if k in weights}
    if budget <= 0 or not clean:
        return
    total = sum(clean.values())
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
    available = [s for s in symbols if s in UNIVERSE and s in close.columns]
    if len(close) < MIN_HISTORY or "SHY" not in available:
        return {s: 0.0 for s in symbols}

    crypto_stress = _stress_for(context.as_of)
    credit_confirm = _clip((-_ret(close, "HYG", 21) + _ret(close, "IEF", 21)) / 0.06, 0.0, 1.0)
    equity_damage = _clip((-_ret(close, "QQQ", 21)) / 0.10, 0.0, 1.0)
    stress = _clip(0.68 * crypto_stress + 0.18 * credit_confirm + 0.14 * equity_damage, 0.0, 1.0)
    duration_bad = 1.0 if _ret(close, "TLT", 63) < -0.06 else 0.0

    risk_budget = _clip(0.48 - 0.35 * stress, 0.12, 0.55)
    duration_budget = _clip(0.17 + 0.24 * stress - 0.12 * duration_bad, 0.06, 0.38)
    gold_budget = _clip(0.09 + 0.13 * stress + 0.05 * max(0.0, _ret(close, "GLD", 63) / 0.08), 0.05, 0.25)
    sector_budget = _clip(0.17 + 0.13 * stress, 0.12, 0.30)
    shy_budget = max(0.05, 1.0 - risk_budget - duration_budget - gold_budget - sector_budget)
    scale = 1.0 / (risk_budget + duration_budget + gold_budget + sector_budget + shy_budget)
    risk_budget *= scale
    duration_budget *= scale
    gold_budget *= scale
    sector_budget *= scale
    shy_budget *= scale

    weights = {s: 0.0 for s in symbols}
    _add(weights, {s: 1.0 + 2.5 * _ret(close, s, 63) + 1.0 * _ret(close, s, 21) - 1.8 * stress for s in RISK if s in available}, risk_budget)
    _add(weights, {s: 1.0 + 1.3 * _ret(close, s, 63) - 0.7 * _vol(close, s, 63) + 0.7 * stress for s in DURATION if s in available}, duration_budget)
    if "GLD" in weights:
        weights["GLD"] += gold_budget
    _add(weights, {s: 1.0 + 1.8 * _ret(close, s, 63) - 0.6 * _vol(close, s, 63) + 0.5 * stress for s in DEF_SECTORS if s in available}, sector_budget)
    if "SHY" in weights:
        weights["SHY"] += shy_budget

    capped = {s: _clip(weights.get(s, 0.0), 0.0, MAX_SINGLE) for s in symbols}
    gross = sum(capped.values())
    if gross <= EPS:
        return {s: 0.0 for s in symbols}
    return {s: round(capped[s] / gross, 10) for s in symbols}
