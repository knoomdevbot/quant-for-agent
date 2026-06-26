"""AR-085 ETF opening-range liquidity reversal after index-futures shock.

QFA-compatible research model exposing ``generate_signals(context)``.  It uses
only OHLCV bars supplied in ``context.prices`` (normally Alpaca/qfa real 1Min
bars).  The rule waits until a completed opening range is available, identifies
broad ETF overnight gaps, and fades gap direction only when the ETF fails to
extend the opening range in the direction of the opening shock.

The model is intentionally flat when called on daily bars or outside the opening
range decision window; it is a microstructure/liquidity-reversal rule, not a
slow regime allocator.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

UNIVERSE = ("SPY", "QQQ", "IWM", "TLT", "IEF", "GLD", "XLU", "XLE", "XLV")
RISK_ETFS = ("SPY", "QQQ", "IWM", "XLE", "XLV")
DEFENSIVE_ETFS = ("TLT", "IEF", "GLD", "XLU")


class Params:
    open_range_minutes = 60
    min_gap_abs = 0.0075
    strong_gap_abs = 0.015
    max_extension = 0.0025
    shock_breadth_min = 0.33
    max_gross = 1.0
    max_single = 0.25
    signal_start_utc_minute = 14 * 60 + 30  # 10:30 NY during EDT, 09:30 during EST guard is broad below.
    signal_end_utc_minute = 18 * 60 + 30
    flat_after_utc_minute = 20 * 60 + 45


PARAMS = Params()


def _flat(symbols) -> dict[str, float]:
    return {s: 0.0 for s in symbols}


def _as_utc(ts) -> pd.Timestamp | None:
    try:
        out = pd.Timestamp(ts)
    except Exception:
        return None
    if out.tzinfo is None:
        out = out.tz_localize("UTC")
    else:
        out = out.tz_convert("UTC")
    return out


def _ny_date(ts: pd.Timestamp):
    return ts.tz_convert("America/New_York").date()


def _ny_minutes(ts: pd.Timestamp) -> int:
    ny = ts.tz_convert("America/New_York")
    return ny.hour * 60 + ny.minute


def _in_decision_window(ts: pd.Timestamp) -> bool:
    # Regular US equity session after a 60-minute opening range and before late-day flattening.
    m = _ny_minutes(ts)
    return (10 * 60 + 30) <= m <= (15 * 60 + 45)


def _safe_float(x, default=0.0) -> float:
    try:
        y = float(x)
    except Exception:
        return default
    return y if math.isfinite(y) else default


def _normalize(raw: dict[str, float], symbols: list[str]) -> dict[str, float]:
    vals = pd.Series({s: _safe_float(raw.get(s, 0.0)) for s in symbols}, dtype=float).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    vals = vals.clip(-PARAMS.max_single, PARAMS.max_single)
    gross = float(vals.abs().sum())
    if gross <= 0:
        return _flat(symbols)
    if gross > PARAMS.max_gross:
        vals *= PARAMS.max_gross / gross
    return {s: float(vals.get(s, 0.0)) for s in symbols}


def _state(prices: pd.DataFrame, symbols: list[str], as_of: pd.Timestamp):
    if prices is None or prices.empty:
        return None
    df = prices[prices["symbol"].isin(symbols)].copy()
    if df.empty or not {"timestamp", "symbol", "open", "high", "low", "close"}.issubset(df.columns):
        return None
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df[df["timestamp"] <= as_of].sort_values(["timestamp", "symbol"])
    if df.empty:
        return None
    df["ny_date"] = df["timestamp"].dt.tz_convert("America/New_York").dt.date
    today = _ny_date(as_of)
    dates = sorted(df["ny_date"].dropna().unique())
    if today not in dates:
        return None
    prev_dates = [d for d in dates if d < today]
    if not prev_dates:
        return None
    prev = df[df["ny_date"] == prev_dates[-1]].groupby("symbol").tail(1).set_index("symbol")
    cur = df[df["ny_date"] == today]
    # Alpaca minute bars are timestamped in UTC; use NY clock to isolate regular session opening range.
    cur = cur.assign(ny_min=cur["timestamp"].dt.tz_convert("America/New_York").dt.hour * 60 + cur["timestamp"].dt.tz_convert("America/New_York").dt.minute)
    regular = cur[(cur["ny_min"] >= 9 * 60 + 30) & (cur["ny_min"] <= _ny_minutes(as_of))]
    opening = regular[(regular["ny_min"] >= 9 * 60 + 30) & (regular["ny_min"] < 10 * 60 + 30)]
    if opening.empty or regular.empty:
        return None
    open_px = opening.groupby("symbol").head(1).set_index("symbol")["open"]
    open_high = opening.groupby("symbol")["high"].max()
    open_low = opening.groupby("symbol")["low"].min()
    last = regular.groupby("symbol").tail(1).set_index("symbol")
    prev_close = prev["close"]
    return prev_close, open_px, open_high, open_low, last


def generate_signals(context) -> dict[str, float]:
    symbols_out = list(getattr(context, "symbols", []) or [])
    weights = _flat(symbols_out)
    as_of = _as_utc(getattr(context, "as_of", None))
    if as_of is None or not _in_decision_window(as_of):
        return weights
    symbols = [s for s in symbols_out if s in UNIVERSE]
    if len(symbols) < 5:
        return weights
    st = _state(getattr(context, "prices", None), symbols, as_of)
    if st is None:
        return weights
    prev_close, open_px, open_high, open_low, last = st
    common = [s for s in symbols if s in prev_close.index and s in open_px.index and s in last.index]
    if len(common) < 5:
        return weights
    gap = (open_px[common] / prev_close[common] - 1.0).replace([np.inf, -np.inf], np.nan).dropna()
    if gap.empty:
        return weights
    shock_mask = gap.abs() >= PARAMS.min_gap_abs
    shock_breadth = float(shock_mask.mean())
    if shock_breadth < PARAMS.shock_breadth_min:
        return weights
    shock_dir = 1.0 if float(gap[shock_mask].median()) > 0 else -1.0
    raw = {s: 0.0 for s in symbols_out}
    for s in gap.index:
        g = _safe_float(gap.get(s))
        if abs(g) < PARAMS.min_gap_abs or math.copysign(1.0, g) != shock_dir:
            continue
        px = _safe_float(last.loc[s, "close"])
        if g > 0:
            extension = px / _safe_float(open_high.get(s)) - 1.0
            failed = extension <= PARAMS.max_extension
            side = -1.0
        else:
            extension = _safe_float(open_low.get(s)) / px - 1.0
            failed = extension <= PARAMS.max_extension
            side = 1.0
        if not failed:
            continue
        # Larger gaps and broad shocks receive more budget, but single-name caps keep the basket diversified.
        strength = min(1.0, abs(g) / PARAMS.strong_gap_abs) * min(1.0, shock_breadth / 0.67)
        raw[s] = side * (0.10 + 0.20 * strength)
    # If equity index shock is broad, add small balancing sleeves in defensive assets in the opposite macro direction.
    active_gross = sum(abs(v) for v in raw.values())
    if active_gross > 0 and shock_dir > 0:
        for s in DEFENSIVE_ETFS:
            if s in symbols_out and raw.get(s, 0.0) == 0.0:
                raw[s] = 0.04
    elif active_gross > 0 and shock_dir < 0:
        for s in DEFENSIVE_ETFS:
            if s in symbols_out and raw.get(s, 0.0) == 0.0:
                raw[s] = -0.04
    return _normalize(raw, symbols_out)
