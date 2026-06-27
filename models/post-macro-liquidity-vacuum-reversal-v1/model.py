"""AR-053 post-macro liquidity-vacuum ETF reversal model.

QFA-compatible research alpha using only OHLCV bars supplied by qfa.  The
signal is intentionally sparse: after deterministic scheduled-macro proxy dates
with abnormal same-day high-low range expansion, it buys the ETF sleeves that
look most liquidity-stressed/lagging for a short 1-3 session reversal window.
"""

from __future__ import annotations

import math
from typing import Dict

import pandas as pd

UNIVERSE = ("SPY", "QQQ", "IWM", "TLT", "GLD", "XLU", "XLE")
CORE_EVENT_ASSETS = ("SPY", "TLT", "GLD")
MIN_HISTORY = 90
RANGE_LOOKBACK = 60
VOL_LOOKBACK = 40
HOLDING_DECAY = (1.00, 0.55, 0.25)  # event day close for next 1, 2, 3 sessions
MAX_SINGLE_NAME = 0.50
MIN_EVENT_RANGE_Z = 0.85
MIN_CORE_RANGE_MULTIPLE = 1.18


def _safe_float(value, default: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return default
    return out if math.isfinite(out) else default


def _clip(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _is_first_friday(ts: pd.Timestamp) -> bool:
    return ts.weekday() == 4 and 1 <= ts.day <= 7


def _is_cpi_proxy(ts: pd.Timestamp) -> bool:
    return ts.weekday() < 5 and 10 <= ts.day <= 14


def _is_fomc_proxy(ts: pd.Timestamp) -> bool:
    # Regular FOMC months; third Wednesday +/- one business day via Tue-Thu days 15-22.
    return ts.month in {1, 3, 5, 6, 7, 9, 11, 12} and ts.weekday() in {1, 2, 3} and 15 <= ts.day <= 22


def _is_mid_quarter_liquidity_proxy(ts: pd.Timestamp) -> bool:
    return ts.month in {2, 5, 8, 11} and ts.weekday() < 5 and 13 <= ts.day <= 17


def _is_scheduled_macro_proxy(ts: pd.Timestamp) -> bool:
    return (
        _is_first_friday(ts)
        or _is_cpi_proxy(ts)
        or _is_fomc_proxy(ts)
        or _is_mid_quarter_liquidity_proxy(ts)
    )


def _normalize_capped(scores: Dict[str, float]) -> Dict[str, float]:
    scores = {k: max(0.0, _safe_float(v)) for k, v in scores.items()}
    total = sum(scores.values())
    if total <= 1e-12:
        return {k: 0.0 for k in scores}
    weights = {k: v / total for k, v in scores.items()}
    for _ in range(4):
        excess = sum(max(0.0, w - MAX_SINGLE_NAME) for w in weights.values())
        if excess <= 1e-12:
            break
        capped = {k for k, w in weights.items() if w >= MAX_SINGLE_NAME}
        for k in capped:
            weights[k] = min(weights[k], MAX_SINGLE_NAME)
        uncapped = {k: scores[k] for k in weights if k not in capped and scores[k] > 0}
        denom = sum(uncapped.values())
        if denom <= 1e-12:
            break
        for k, v in uncapped.items():
            weights[k] += excess * v / denom
    return weights


def _event_scores(close: pd.DataFrame, high: pd.DataFrame, low: pd.DataFrame, event_pos: int, available: list[str]) -> Dict[str, float]:
    if event_pos < MIN_HISTORY:
        return {}
    event_ts = close.index[event_pos]
    if not _is_scheduled_macro_proxy(event_ts):
        return {}

    prev_close = close.iloc[event_pos - 1]
    event_close = close.iloc[event_pos]
    event_high = high.iloc[event_pos]
    event_low = low.iloc[event_pos]
    day_ret = (event_close / prev_close - 1.0).replace([math.inf, -math.inf], pd.NA)
    range_pct = ((event_high - event_low) / prev_close).replace([math.inf, -math.inf], pd.NA)
    hist_range = ((high.iloc[event_pos - RANGE_LOOKBACK : event_pos] - low.iloc[event_pos - RANGE_LOOKBACK : event_pos]) / close.shift(1).iloc[event_pos - RANGE_LOOKBACK : event_pos]).replace([math.inf, -math.inf], pd.NA)

    range_z: Dict[str, float] = {}
    for s in available:
        hist = hist_range[s].dropna() if s in hist_range.columns else pd.Series(dtype=float)
        if len(hist) < 30:
            range_z[s] = 0.0
            continue
        sd = _safe_float(hist.std(ddof=1))
        range_z[s] = 0.0 if sd <= 1e-12 else _clip((_safe_float(range_pct.get(s)) - _safe_float(hist.mean())) / sd, -3.0, 3.0)

    core_values = [_safe_float(range_pct.get(s)) / max(_safe_float(hist_range[s].median()), 1e-9) for s in CORE_EVENT_ASSETS if s in available and s in hist_range]
    core_multiple = sum(core_values) / len(core_values) if core_values else 0.0
    avg_range_z = sum(max(0.0, range_z.get(s, 0.0)) for s in CORE_EVENT_ASSETS if s in available) / max(sum(1 for s in CORE_EVENT_ASSETS if s in available), 1)
    if avg_range_z < MIN_EVENT_RANGE_Z or core_multiple < MIN_CORE_RANGE_MULTIPLE:
        return {}

    basket_ret = sum(_safe_float(day_ret.get(s)) for s in available) / max(len(available), 1)
    scores: Dict[str, float] = {}
    for s in available:
        rng = max(_safe_float(event_high.get(s) - event_low.get(s)), 1e-9)
        close_location = _clip(_safe_float((event_close.get(s) - event_low.get(s)) / rng), 0.0, 1.0)
        lag = max(0.0, basket_ret - _safe_float(day_ret.get(s)))
        poor_close = 1.0 - close_location
        vol = close[s].pct_change().iloc[max(0, event_pos - VOL_LOOKBACK) : event_pos].std(ddof=1)
        inv_vol = 1.0 / max(_safe_float(vol), 0.006)
        raw = (0.65 * _clip(lag / 0.018, 0.0, 2.0) + 0.25 * poor_close + 0.10 * max(0.0, range_z.get(s, 0.0))) * inv_vol
        if raw > 0:
            scores[s] = raw

    # Keep only the most stressed laggards; this reduces beta-like always-on exposure.
    top = dict(sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:3])
    return _normalize_capped(top)


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
    if len(available) < 5:
        return {s: 0.0 for s in symbols}

    combined = {s: 0.0 for s in available}
    last_pos = len(close) - 1
    for age, decay in enumerate(HOLDING_DECAY):
        event_pos = last_pos - age
        if event_pos < MIN_HISTORY:
            continue
        event_weights = _event_scores(close, high, low, event_pos, available)
        for s, w in event_weights.items():
            combined[s] += decay * w

    weights = _normalize_capped({s: v for s, v in combined.items() if v > 0})
    return {s: _safe_float(weights.get(s, 0.0)) for s in symbols}
