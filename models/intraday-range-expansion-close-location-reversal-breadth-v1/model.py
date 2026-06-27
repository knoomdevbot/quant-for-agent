"""AR-079 intraday range-expansion close-location reversal breadth.

QFA-compatible research model exposing generate_signals(context).  It uses only
OHLCV bars supplied by qfa/Alpaca.  The rule is intraday-only: it forms signals
from completed regular-session minute bars and returns flat outside the intended
short holding window.

Mechanism: broad ETF range expansion with closes near the bar extremes is treated
as a liquidity-flow exhaustion event.  If breadth is downside extreme, the model
fades by buying risk/sector ETFs and underweighting defensive sleeves; upside
extremes are faded in the opposite direction.  Gross exposure is capped at 1.0.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

UNIVERSE = ("SPY", "QQQ", "IWM", "XLV", "XLY", "XLE", "XLU", "XLP", "TLT", "IEF", "GLD", "HYG", "LQD", "SHY")
RISK = ("SPY", "QQQ", "IWM", "XLV", "XLY", "XLE", "HYG")
DEFENSIVE = ("TLT", "IEF", "GLD", "LQD", "SHY", "XLU", "XLP")


class Params:
    """Plain parameter container.

    qfa imports model modules with importlib without registering them in
    sys.modules, which makes dataclasses with postponed annotations fail under
    Python 3.11.  A simple class keeps the artifact qfa-loadable.
    """

    range_window = 20
    breadth_window = 10
    min_history = 80
    close_location_tail = 0.25
    expansion_multiple = 1.35
    breadth_trigger = 0.35
    min_net_breadth = 0.20
    max_gross = 1.0
    max_single = 0.18
    hold_bars = 3
    late_session_flat_utc_hour = 20
    late_session_flat_utc_minute = 45


PARAMS = Params()


def _flat(symbols: list[str]) -> dict[str, float]:
    return {s: 0.0 for s in symbols}


def _to_utc(ts) -> pd.Timestamp | None:
    try:
        out = pd.Timestamp(ts)
    except Exception:
        return None
    if out.tzinfo is None:
        out = out.tz_localize("UTC")
    else:
        out = out.tz_convert("UTC")
    return out


def _regular_session(ts: pd.Timestamp) -> bool:
    # US regular equity session in UTC for the 2023-2025 sample: 13:30/14:30 to 20:00/21:00.
    # Use a broad guard to include both DST and standard time without external calendars.
    hm = ts.hour * 60 + ts.minute
    return (13 * 60 + 30) <= hm <= (21 * 60)


def _too_late(ts: pd.Timestamp, p: Params) -> bool:
    return (ts.hour * 60 + ts.minute) >= (p.late_session_flat_utc_hour * 60 + p.late_session_flat_utc_minute)


def _normalize(raw: dict[str, float], symbols: list[str], max_gross: float, max_single: float) -> dict[str, float]:
    vals = pd.Series({s: float(raw.get(s, 0.0)) for s in symbols}, dtype=float).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    vals = vals.clip(lower=-max_single, upper=max_single)
    gross = float(vals.abs().sum())
    if gross <= 0:
        return _flat(symbols)
    if gross > max_gross:
        vals *= max_gross / gross
    return {s: float(vals.get(s, 0.0)) for s in symbols}


def _latest_intraday_state(prices: pd.DataFrame, symbols: list[str], as_of: pd.Timestamp, p: Params):
    df = prices[prices["symbol"].isin(symbols)].copy()
    if df.empty:
        return None
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df[df["timestamp"] <= as_of].sort_values(["timestamp", "symbol"])
    # Keep a compact recent tail for qfa speed.
    recent_times = df["timestamp"].drop_duplicates().tail(max(p.min_history + 20, 140))
    df = df[df["timestamp"].isin(recent_times)]
    wide = {}
    for col in ("open", "high", "low", "close"):
        if col not in df.columns:
            return None
        wide[col] = df.pivot(index="timestamp", columns="symbol", values=col).sort_index().ffill()
    close = wide["close"].dropna(axis=1, how="any")
    tradable = [s for s in symbols if s in close.columns]
    if len(tradable) < 8 or len(close) < p.min_history:
        return None
    high = wide["high"][tradable]
    low = wide["low"][tradable]
    close = wide["close"][tradable]
    return high, low, close, tradable


def generate_signals(context) -> dict[str, float]:
    symbols_out = list(getattr(context, "symbols", []) or [])
    symbols = [s for s in symbols_out if s in UNIVERSE]
    weights = _flat(symbols_out)
    as_of = _to_utc(getattr(context, "as_of", None))
    if as_of is None or not _regular_session(as_of) or _too_late(as_of, PARAMS):
        return weights
    prices = getattr(context, "prices", None)
    if prices is None or prices.empty:
        return weights
    state = _latest_intraday_state(prices, symbols, as_of, PARAMS)
    if state is None:
        return weights
    high, low, close, tradable = state
    p = PARAMS
    rng = (high - low).replace(0.0, np.nan)
    clv = ((close - low) / rng).clip(0.0, 1.0)
    bar_ret = close.pct_change().replace([np.inf, -np.inf], np.nan)
    median_range = rng.shift(1).rolling(p.range_window, min_periods=p.range_window).median()
    expansion = rng / median_range
    latest = close.index[-1]
    if latest != as_of and latest > as_of:
        return weights

    down_extreme = (expansion >= p.expansion_multiple) & (clv <= p.close_location_tail) & (bar_ret < 0)
    up_extreme = (expansion >= p.expansion_multiple) & (clv >= 1.0 - p.close_location_tail) & (bar_ret > 0)
    down_breadth = down_extreme.tail(p.breadth_window).mean(axis=1).iloc[-1]
    up_breadth = up_extreme.tail(p.breadth_window).mean(axis=1).iloc[-1]
    if not (math.isfinite(float(down_breadth)) and math.isfinite(float(up_breadth))):
        return weights
    net = float(down_breadth - up_breadth)
    if abs(net) < p.min_net_breadth or max(float(down_breadth), float(up_breadth)) < p.breadth_trigger:
        return weights

    # Fade the breadth extreme.  Recent symbol-specific extremes get larger allocations.
    risk_avail = [s for s in RISK if s in tradable]
    def_avail = [s for s in DEFENSIVE if s in tradable]
    if len(risk_avail) < 3 or len(def_avail) < 3:
        return weights
    intensity = min(1.0, abs(net) / 0.60)
    raw = {s: 0.0 for s in symbols_out}
    if net > 0:  # downside range/close-location exhaustion: long risk, short defensive.
        for s in risk_avail:
            bonus = 1.0 + float(down_extreme[s].tail(p.hold_bars).sum())
            raw[s] = 0.70 * intensity * bonus / len(risk_avail)
        for s in def_avail:
            raw[s] = -0.30 * intensity / len(def_avail)
    else:  # upside exhaustion: reduce risk, own defensive sleeves.
        for s in risk_avail:
            bonus = 1.0 + float(up_extreme[s].tail(p.hold_bars).sum())
            raw[s] = -0.70 * intensity * bonus / len(risk_avail)
        for s in def_avail:
            raw[s] = 0.30 * intensity / len(def_avail)
    return _normalize(raw, symbols_out, p.max_gross, p.max_single)
