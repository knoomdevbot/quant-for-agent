"""AR-123 Treasury payment-day duration ETF reinvestment drift.

QFA-compatible research model exposing generate_signals(context) -> dict[str, float].
The signal is deliberately ex-ante and calendar-only: allocate equally to a fixed
basket of direct Treasury duration ETFs on deterministic Treasury coupon/principal
payment trading dates (15th and month-end contractual payment dates, business-day
adjusted). It uses qfa/Alpaca daily OHLCV only for tradability/history checks and
never submits orders.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, timedelta

import pandas as pd

CANDIDATE_POOL = ("TLT", "IEF", "SHY", "GOVT", "TIP", "EDV", "ZROZ", "LQD", "HYG", "BIL", "SGOV")
SELECTED_UNIVERSE = ("TLT", "IEF", "SHY", "GOVT", "TIP", "EDV", "ZROZ")
CONTROL_SYMBOLS = ("LQD", "HYG", "BIL", "SGOV")


@dataclass(frozen=True)
class Params:
    min_history: int = 80
    gross: float = 1.0


PARAMS = Params()


def _zero(symbols: list[str]) -> dict[str, float]:
    return {s: 0.0 for s in symbols}


def _observed_us_holidays(year: int) -> set[date]:
    """NYSE/Treasury-like weekday holiday approximation sufficient for calendar gating."""

    def obs(d: date) -> date:
        if d.weekday() == 5:
            return d - timedelta(days=1)
        if d.weekday() == 6:
            return d + timedelta(days=1)
        return d

    def nth_weekday(month: int, weekday: int, n: int) -> date:
        d = date(year, month, 1)
        return d + timedelta(days=((weekday - d.weekday()) % 7) + 7 * (n - 1))

    def last_weekday(month: int, weekday: int) -> date:
        d = date(year, month, calendar.monthrange(year, month)[1])
        return d - timedelta(days=(d.weekday() - weekday) % 7)

    # Good Friday (Anonymous Gregorian algorithm for Easter Sunday minus two days).
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    letter_l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * letter_l) // 451
    easter_month = (h + letter_l - 7 * m + 114) // 31
    easter_day = ((h + letter_l - 7 * m + 114) % 31) + 1
    good_friday = date(year, easter_month, easter_day) - timedelta(days=2)

    holidays = {
        obs(date(year, 1, 1)),
        nth_weekday(1, 0, 3),
        nth_weekday(2, 0, 3),
        good_friday,
        last_weekday(5, 0),
        obs(date(year, 6, 19)),
        obs(date(year, 7, 4)),
        nth_weekday(9, 0, 1),
        nth_weekday(11, 3, 4),
        obs(date(year, 12, 25)),
    }
    return holidays


def _next_business_day(d: date) -> date:
    holidays = _observed_us_holidays(d.year) | _observed_us_holidays(d.year + 1)
    while d.weekday() >= 5 or d in holidays:
        d += timedelta(days=1)
    return d


def payment_dates(year: int) -> set[date]:
    """Ex-ante Treasury coupon/principal payment-date proxy.

    Assumption: marketable Treasury note/bond/FRN/TIPS coupon and principal cash
    flows cluster on contractual 15th and end-of-month dates; if that date is not a
    business/trading day, payment is made on the next business day. Bill maturities
    and security-specific CUSIP cash-flow magnitudes are intentionally not inferred
    from prices and are excluded from the primary signal.
    """

    out: set[date] = set()
    for month in range(1, 13):
        out.add(_next_business_day(date(year, month, 15)))
        out.add(_next_business_day(date(year, month, calendar.monthrange(year, month)[1])))
    return out


def is_payment_date(ts: pd.Timestamp) -> bool:
    d = pd.Timestamp(ts).date()
    return d in (payment_dates(d.year) | payment_dates(d.year - 1))


def generate_signals(context) -> dict[str, float]:
    output_symbols = list(getattr(context, "symbols", []) or [])
    prices = getattr(context, "prices", pd.DataFrame())
    if prices.empty:
        return _zero(output_symbols)
    df = prices[prices["symbol"].isin(SELECTED_UNIVERSE)].copy()
    if df.empty:
        return _zero(output_symbols)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    close = df.pivot(index="timestamp", columns="symbol", values="close").sort_index().ffill()
    if len(close) < PARAMS.min_history or not is_payment_date(close.index[-1]):
        return _zero(output_symbols)
    tradable = [s for s in SELECTED_UNIVERSE if s in output_symbols and s in close.columns and pd.notna(close[s].iloc[-1])]
    if not tradable:
        return _zero(output_symbols)
    w = PARAMS.gross / len(tradable)
    return {s: (w if s in tradable else 0.0) for s in output_symbols}
