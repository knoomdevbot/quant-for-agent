"""AR-131 EIA petroleum inventory release-day energy ETF allocator.

QFA contract: expose generate_signals(context) -> dict[str, float]. Equal-weight
long fixed basket only on deterministic approximated EIA Petroleum Status Report
release dates. No inventory surprises, CSV input, daemon state, or orders.
"""

from __future__ import annotations

from datetime import timedelta

import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar

SELECTED_SYMBOLS = ["XLE", "VDE", "IYE", "XOP", "OIH", "USO", "BNO", "DBC"]
MAX_GROSS_EXPOSURE = 1.0


def _as_of_date(context):
    as_of = getattr(context, "as_of", None)
    if as_of is not None:
        return pd.Timestamp(as_of).date()

    prices = getattr(context, "prices", None)
    if prices is None or getattr(prices, "empty", True) or "timestamp" not in prices:
        return None

    return pd.to_datetime(prices["timestamp"], utc=True).max().date()


def _is_approx_eia_release(day):
    if day.weekday() not in (2, 3):
        return False

    wednesday = day if day.weekday() == 2 else day - timedelta(days=1)
    holidays = set(
        USFederalHolidayCalendar()
        .holidays(start=str(wednesday - timedelta(days=7)), end=str(wednesday + timedelta(days=7)))
        .date
    )
    shifted = any((wednesday - timedelta(days=offset)) in holidays for offset in (0, 1, 2))
    expected_release_day = wednesday + timedelta(days=1) if shifted else wednesday
    return day == expected_release_day


def generate_signals(context):
    """Return equal-weight long energy ETF basket on approximated EIA release dates."""
    symbols = list(getattr(context, "symbols", []) or SELECTED_SYMBOLS)
    weights = {symbol: 0.0 for symbol in symbols}
    as_of = _as_of_date(context)
    if as_of is None or not _is_approx_eia_release(as_of):
        return weights

    active = [symbol for symbol in SELECTED_SYMBOLS if symbol in symbols]
    if not active:
        return weights

    weight = MAX_GROSS_EXPOSURE / len(active)
    for symbol in active:
        weights[symbol] = weight
    return weights
