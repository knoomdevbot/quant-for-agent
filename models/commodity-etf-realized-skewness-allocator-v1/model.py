"""AR-111 commodity ETF realized-skewness cross-sectional allocator.

QFA contract: expose generate_signals(context) -> dict[str, float].

Hypothesis: among a fixed ex-ante universe of pure commodity ETF/ETN
proxies, low trailing realized daily-return skewness should outperform
high-skewness lottery-like commodity exposures on a monthly cross-sectional
basis.  The model is intentionally simple, lagged, and rule based.
"""
from __future__ import annotations

import math
from typing import Dict

import pandas as pd

# Fixed ex-ante pure commodity ETF/ETN universe; sector-equity proxies are not
# traded by the primary model and are diagnostic-only in the evaluation.
UNIVERSE = ("GLD", "SLV", "USO", "UNG", "DBA", "DBC", "CPER", "CORN", "WEAT", "SOYB", "PALL", "PPLT")
LOOKBACK_DAYS = 252
MIN_OBS = 210
REBALANCE_DAY_MIN = 25  # rebalance near first observed trading day of each month
MAX_ABS_WEIGHT = 0.20
TARGET_GROSS = 1.0


def _close_matrix(context) -> pd.DataFrame:
    prices = getattr(context, "prices", None)
    if prices is None or prices.empty:
        return pd.DataFrame()
    p = prices.copy()
    p["timestamp"] = pd.to_datetime(p["timestamp"], utc=True)
    return p.pivot(index="timestamp", columns="symbol", values="close").sort_index().ffill()


def _month_rebalance_slice(close: pd.DataFrame) -> pd.DataFrame:
    """Hold weights between monthly rebalances in a stateless qfa model.

    qfa calls generate_signals daily without persisted state.  To approximate
    monthly weights, freeze the information set at the first available trading
    day of the current month; before that date has enough data, use the latest
    prior month-end anchor.
    """
    if close.empty:
        return close
    idx = close.index
    asof = idx[-1]
    monthly_firsts = idx.to_series().groupby(idx.to_period("M")).first().sort_values()
    anchors = monthly_firsts[monthly_firsts <= asof]
    if anchors.empty:
        return close.iloc[:1]
    anchor = anchors.iloc[-1]
    return close.loc[:anchor]


def _safe_skew(x: pd.Series) -> float | None:
    x = x.dropna().tail(LOOKBACK_DAYS)
    if len(x) < MIN_OBS:
        return None
    sd = float(x.std(ddof=1))
    if not math.isfinite(sd) or sd <= 1e-12:
        return None
    val = float(x.skew())
    return val if math.isfinite(val) else None


def _vol(x: pd.Series) -> float | None:
    x = x.dropna().tail(LOOKBACK_DAYS)
    if len(x) < MIN_OBS:
        return None
    val = float(x.std(ddof=1) * math.sqrt(252.0))
    return val if math.isfinite(val) and val > 0 else None


def _normalize(raw: Dict[str, float], output_symbols: list[str]) -> dict[str, float]:
    weights = {s: 0.0 for s in output_symbols}
    for s, w in raw.items():
        if s in weights:
            weights[s] = max(-MAX_ABS_WEIGHT, min(MAX_ABS_WEIGHT, float(w)))
    gross = sum(abs(w) for w in weights.values())
    if gross <= 1e-12:
        return weights
    scale = min(TARGET_GROSS / gross, 1.0)
    return {s: float(w * scale) for s, w in weights.items()}


def generate_signals(context) -> dict[str, float]:
    output_symbols = list(getattr(context, "symbols", []) or [])
    weights = {s: 0.0 for s in output_symbols}
    close_all = _close_matrix(context)
    close = _month_rebalance_slice(close_all)
    if len(close) < MIN_OBS + 2:
        return weights

    available = [s for s in UNIVERSE if s in output_symbols and s in close.columns]
    scores: dict[str, tuple[float, float]] = {}
    for s in available:
        rets = close[s].pct_change().dropna()
        skew = _safe_skew(rets)
        vol = _vol(rets)
        if skew is not None and vol is not None:
            scores[s] = (skew, vol)
    if len(scores) < 6:
        return weights

    # Long the lower-skewness tercile and short the higher-skewness tercile.
    ranked = sorted(scores, key=lambda s: scores[s][0])
    bucket = max(2, len(ranked) // 3)
    longs = ranked[:bucket]
    shorts = ranked[-bucket:]
    raw: dict[str, float] = {}

    # Equal-vol within buckets to avoid allowing UNG/USO volatility to dominate.
    inv_long = {s: 1.0 / max(scores[s][1], 0.05) for s in longs}
    inv_short = {s: 1.0 / max(scores[s][1], 0.05) for s in shorts}
    long_sum = sum(inv_long.values())
    short_sum = sum(inv_short.values())
    for s in longs:
        raw[s] = 0.5 * inv_long[s] / long_sum if long_sum > 0 else 0.0
    for s in shorts:
        raw[s] = raw.get(s, 0.0) - (0.5 * inv_short[s] / short_sum if short_sum > 0 else 0.0)
    return _normalize(raw, output_symbols)
