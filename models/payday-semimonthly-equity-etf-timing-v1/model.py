"""AR-110 payday/semi-monthly contribution-flow equity ETF timing model.

Rule: hold SPY for the first tradable session on or after the 16th calendar
day of each month, approximated live by entering near the prior completed
session when the next business day is calendar day >= 16. Research only: no
orders, no daemon requirement, gross exposure <= 1.0.
"""
from __future__ import annotations

from typing import Any
import pandas as pd

CANDIDATE_POOL = ("SPY", "VOO", "VTI", "QQQ", "IWM", "DIA", "XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "IWF", "IWD", "MTUM", "VLUE", "QUAL", "USMV")
SELECTED_UNIVERSE = ("SPY",)
GROSS_EXPOSURE = 1.0
EVENT_CALENDAR_DAY = 16


def _zero(symbols: list[str]) -> dict[str, float]:
    return {s: 0.0 for s in symbols}


def _last_timestamp(prices: pd.DataFrame) -> pd.Timestamp | None:
    if prices is None or len(prices) == 0 or "timestamp" not in prices:
        return None
    ts = pd.to_datetime(prices["timestamp"], utc=True, errors="coerce").dropna()
    if ts.empty:
        return None
    return ts.max()


def _is_pre_event_session(as_of: pd.Timestamp) -> bool:
    """Approximate whether next business session is first tradable >= day 16.

    qfa supplies completed bars but not an exchange-holiday calendar.  This live
    rule uses the next pandas business day as a durable deterministic proxy; the
    research evaluation computes exact event days from observed Alpaca sessions.
    """
    d = as_of.tz_convert("UTC").normalize().tz_localize(None)
    nxt = d + pd.offsets.BDay(1)
    if nxt.day < EVENT_CALENDAR_DAY:
        return False
    # The previous business day before the event must be before the 16th, or in
    # the prior month when the first available >=16 follows a weekend/holiday.
    return d.month == nxt.month and d.day < EVENT_CALENDAR_DAY


def generate_signals(context: Any) -> dict[str, float]:
    symbols = list(getattr(context, "symbols", []) or [])
    weights = _zero(symbols)
    if "SPY" not in symbols:
        return weights
    as_of = getattr(context, "as_of", None)
    if as_of is None:
        as_of = _last_timestamp(getattr(context, "prices", pd.DataFrame()))
    if as_of is None:
        return weights
    as_of = pd.Timestamp(as_of)
    if as_of.tzinfo is None:
        as_of = as_of.tz_localize("UTC")
    else:
        as_of = as_of.tz_convert("UTC")
    if _is_pre_event_session(as_of):
        weights["SPY"] = GROSS_EXPOSURE
    return weights
