"""AR-074 macro-event liquidity-gap ETF recovery allocator.

QFA contract: expose generate_signals(context) returning target weights by symbol.
Uses only OHLCV bars supplied by qfa/Alpaca.  Scheduled macro events are a
pure deterministic timestamp-safe proxy (first-Friday payrolls, CPI window,
regular FOMC-month midweek window, and mid-quarter liquidity window); there is
no external calendar and no future data dependency.
"""
from __future__ import annotations

import math
from typing import Dict

import pandas as pd

UNIVERSE = ("SPY", "QQQ", "IWM", "TLT", "GLD", "XLU", "XLE", "SHY")
RISK_ETFS = ("SPY", "QQQ", "IWM", "XLU", "XLE")
DEFENSIVE_ETFS = ("SHY", "TLT", "GLD", "XLU")
CORE_EVENT_ETFS = ("SPY", "QQQ", "IWM", "TLT", "GLD")

MIN_HISTORY = 126
RANGE_LOOKBACK = 63
GAP_LOOKBACK = 63
MOM_LOOKBACK = 20
REV_LOOKBACK = 3
HOLDING_DECAY = (1.00, 0.70, 0.45, 0.25, 0.10)
EVENT_RANGE_Z_MIN = 0.75
EVENT_GAP_Z_MIN = 0.70
UNSCHEDULED_STRESS_Z_MIN = 1.85
MAX_SINGLE_WEIGHT = 0.42
MAX_EVENT_NAMES = 4


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
    # CPI usually falls near the 10th-14th; use business-day window only.
    return ts.weekday() < 5 and 10 <= ts.day <= 14


def _is_fomc_proxy(ts: pd.Timestamp) -> bool:
    # Regular meeting months, Tue-Thu around the third Wednesday.
    return ts.month in {1, 3, 5, 6, 7, 9, 11, 12} and ts.weekday() in {1, 2, 3} and 15 <= ts.day <= 22


def _is_mid_quarter_liquidity_proxy(ts: pd.Timestamp) -> bool:
    return ts.month in {2, 5, 8, 11} and ts.weekday() < 5 and 13 <= ts.day <= 17


def _is_scheduled_macro_proxy(ts: pd.Timestamp) -> bool:
    return _is_first_friday(ts) or _is_cpi_proxy(ts) or _is_fomc_proxy(ts) or _is_mid_quarter_liquidity_proxy(ts)


def _normalize_capped(scores: Dict[str, float], cap: float = MAX_SINGLE_WEIGHT) -> Dict[str, float]:
    scores = {k: max(0.0, _safe_float(v)) for k, v in scores.items() if _safe_float(v) > 0}
    if not scores:
        return {}
    weights = {k: v / sum(scores.values()) for k, v in scores.items()}
    for _ in range(8):
        over = {k: w for k, w in weights.items() if w > cap}
        if not over:
            break
        excess = sum(w - cap for w in over.values())
        for k in over:
            weights[k] = cap
        under = [k for k in weights if weights[k] < cap - 1e-12]
        denom = sum(scores[k] for k in under)
        if denom <= 1e-12:
            break
        for k in under:
            weights[k] += excess * scores[k] / denom
    gross = sum(weights.values())
    return {k: _safe_float(v / gross) for k, v in weights.items()} if gross > 0 else {}


def _event_intensity(close: pd.DataFrame, open_: pd.DataFrame, high: pd.DataFrame, low: pd.DataFrame, pos: int, available: list[str]) -> tuple[float, dict[str, float], dict[str, float]]:
    if pos < MIN_HISTORY:
        return 0.0, {}, {}
    prev_close = close.iloc[pos - 1]
    day_open = open_.iloc[pos]
    day_high = high.iloc[pos]
    day_low = low.iloc[pos]
    gap = (day_open / prev_close - 1.0).replace([math.inf, -math.inf], pd.NA)
    rng = ((day_high - day_low) / prev_close).replace([math.inf, -math.inf], pd.NA)
    hist_gap = (open_.iloc[pos - GAP_LOOKBACK : pos] / close.shift(1).iloc[pos - GAP_LOOKBACK : pos] - 1.0).abs()
    hist_rng = ((high.iloc[pos - RANGE_LOOKBACK : pos] - low.iloc[pos - RANGE_LOOKBACK : pos]) / close.shift(1).iloc[pos - RANGE_LOOKBACK : pos])

    gap_z: dict[str, float] = {}
    range_z: dict[str, float] = {}
    for s in available:
        g_hist = hist_gap[s].dropna() if s in hist_gap else pd.Series(dtype=float)
        r_hist = hist_rng[s].dropna() if s in hist_rng else pd.Series(dtype=float)
        g_sd = _safe_float(g_hist.std(ddof=1)) if len(g_hist) >= 30 else 0.0
        r_sd = _safe_float(r_hist.std(ddof=1)) if len(r_hist) >= 30 else 0.0
        gap_z[s] = _clip((_safe_float(abs(gap.get(s))) - _safe_float(g_hist.mean())) / g_sd, -3.0, 3.0) if g_sd > 1e-12 else 0.0
        range_z[s] = _clip((_safe_float(rng.get(s)) - _safe_float(r_hist.mean())) / r_sd, -3.0, 3.0) if r_sd > 1e-12 else 0.0

    core = [s for s in CORE_EVENT_ETFS if s in available]
    avg_gap_z = sum(max(0.0, gap_z.get(s, 0.0)) for s in core) / max(len(core), 1)
    avg_range_z = sum(max(0.0, range_z.get(s, 0.0)) for s in core) / max(len(core), 1)
    scheduled = _is_scheduled_macro_proxy(close.index[pos])
    if scheduled and (avg_range_z >= EVENT_RANGE_Z_MIN or avg_gap_z >= EVENT_GAP_Z_MIN):
        intensity = 0.55 * avg_range_z + 0.45 * avg_gap_z
    elif (avg_range_z + avg_gap_z) >= UNSCHEDULED_STRESS_Z_MIN:
        # Fallback for timestamp-safe macro-event proxy misses: only when cross-ETF gap/range stress is extreme.
        intensity = 0.35 * (avg_range_z + avg_gap_z)
    else:
        intensity = 0.0
    return _clip(intensity, 0.0, 3.0), gap_z, range_z


def _recovery_scores(close: pd.DataFrame, open_: pd.DataFrame, high: pd.DataFrame, low: pd.DataFrame, pos: int, available: list[str]) -> Dict[str, float]:
    intensity, gap_z, range_z = _event_intensity(close, open_, high, low, pos, available)
    if intensity <= 0.0:
        return {}
    prev_close = close.iloc[pos - 1]
    event_close = close.iloc[pos]
    event_low = low.iloc[pos]
    event_high = high.iloc[pos]
    day_ret = (event_close / prev_close - 1.0).replace([math.inf, -math.inf], pd.NA)
    risk_cols = [s for s in RISK_ETFS if s in available]
    basket_ret = sum(_safe_float(day_ret.get(s)) for s in risk_cols) / max(len(risk_cols), 1)
    scores: Dict[str, float] = {}
    for s in available:
        px = close[s].dropna()
        if len(px) <= max(MOM_LOOKBACK, REV_LOOKBACK) + 2:
            continue
        hl = max(_safe_float(event_high.get(s) - event_low.get(s)), 1e-9)
        close_location = _clip(_safe_float((event_close.get(s) - event_low.get(s)) / hl), 0.0, 1.0)
        lag = max(0.0, basket_ret - _safe_float(day_ret.get(s)))
        short_reversal = max(0.0, _safe_float(px.iloc[-1] / px.iloc[-REV_LOOKBACK] - 1.0))
        prior_drawdown = max(0.0, -_safe_float(px.iloc[-1] / px.iloc[-MOM_LOOKBACK] - 1.0))
        liquidity_stress = max(0.0, gap_z.get(s, 0.0)) + max(0.0, range_z.get(s, 0.0)) + (1.0 - close_location)
        base = 0.40 * _clip(lag / 0.012, 0.0, 2.5) + 0.25 * _clip(prior_drawdown / 0.04, 0.0, 2.0) + 0.20 * _clip(short_reversal / 0.018, 0.0, 2.0) + 0.15 * liquidity_stress
        if s in DEFENSIVE_ETFS and basket_ret < -0.006:
            base *= 1.25
        if s in RISK_ETFS and basket_ret > 0.004:
            base *= 1.15
        if base > 0:
            scores[s] = base * max(0.25, intensity)
    top = dict(sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:MAX_EVENT_NAMES])
    return _normalize_capped(top)


def _fallback_defensive(close: pd.DataFrame, available: list[str]) -> Dict[str, float]:
    # Low-turnover ballast when no event/recovery signal is active.
    candidates = [s for s in DEFENSIVE_ETFS if s in available]
    if not candidates:
        return {}
    scores: Dict[str, float] = {}
    for s in candidates:
        px = close[s].dropna()
        if len(px) < 64:
            continue
        mom = _safe_float(px.iloc[-1] / px.iloc[-63] - 1.0)
        dd = _safe_float(px.iloc[-1] / px.iloc[-63:].max() - 1.0)
        vol = _safe_float(px.pct_change().iloc[-40:].std(ddof=1))
        scores[s] = max(0.01, 0.05 + mom + 0.5 * dd - 0.7 * vol)
    return _normalize_capped(scores, cap=0.60)


def generate_signals(context) -> dict[str, float]:
    symbols = list(context.symbols)
    if context.prices is None or context.prices.empty:
        return {s: 0.0 for s in symbols}
    prices = context.prices.copy()
    prices["timestamp"] = pd.to_datetime(prices["timestamp"], utc=True)
    prices = prices[prices["symbol"].isin(UNIVERSE)].sort_values(["timestamp", "symbol"])
    close = prices.pivot(index="timestamp", columns="symbol", values="close").sort_index().ffill()
    open_ = prices.pivot(index="timestamp", columns="symbol", values="open").sort_index().ffill()
    high = prices.pivot(index="timestamp", columns="symbol", values="high").sort_index().ffill()
    low = prices.pivot(index="timestamp", columns="symbol", values="low").sort_index().ffill()
    available = [s for s in symbols if s in UNIVERSE and s in close.columns]
    if len(close) < MIN_HISTORY or len(available) < 4:
        return {s: 0.0 for s in symbols}

    combined = {s: 0.0 for s in available}
    last_pos = len(close) - 1
    for age, decay in enumerate(HOLDING_DECAY):
        pos = last_pos - age
        if pos < MIN_HISTORY:
            continue
        event_weights = _recovery_scores(close, open_, high, low, pos, available)
        for s, w in event_weights.items():
            combined[s] += decay * w
    event_alloc = _normalize_capped({s: v for s, v in combined.items() if v > 0})
    if event_alloc:
        return {s: _safe_float(event_alloc.get(s, 0.0)) for s in symbols}
    defensive = _fallback_defensive(close, available)
    return {s: _safe_float(defensive.get(s, 0.0)) for s in symbols}
