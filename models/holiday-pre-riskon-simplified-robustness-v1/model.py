"""AR-129 pre-holiday risk-on ETF calendar model.

Rule-only refinement of AR-127: long a fixed broad equity/credit risk-on ETF
basket only on the last tradable NYSE session before predeclared full-day
holidays; zero exposure otherwise. Post-holiday legs are explicitly excluded.
"""
from __future__ import annotations

from datetime import date, timedelta
import pandas as pd
from dateutil.easter import easter

UNIVERSE = ("SPY", "QQQ", "IWM", "MDY", "EFA", "EEM", "HYG", "LQD", "VCIT")
WEIGHT = 1.0 / len(UNIVERSE)


def _nth_weekday(y: int, m: int, weekday: int, n: int) -> date:
    d = date(y, m, 1)
    while d.weekday() != weekday:
        d += timedelta(days=1)
    return d + timedelta(days=7 * (n - 1))


def _last_weekday(y: int, m: int, weekday: int) -> date:
    d = date(y, m + 1, 1) - timedelta(days=1) if m < 12 else date(y, 12, 31)
    while d.weekday() != weekday:
        d -= timedelta(days=1)
    return d


def _observed(d: date) -> date:
    if d.weekday() == 5:
        return d - timedelta(days=1)
    if d.weekday() == 6:
        return d + timedelta(days=1)
    return d


def _holiday_dates(y: int) -> set[date]:
    h = {
        _observed(date(y, 1, 1)),
        _nth_weekday(y, 1, 0, 3),
        _nth_weekday(y, 2, 0, 3),
        easter(y) - timedelta(days=2),
        _last_weekday(y, 5, 0),
        _observed(date(y, 7, 4)),
        _nth_weekday(y, 9, 0, 1),
        _nth_weekday(y, 11, 3, 4),
        _observed(date(y, 12, 25)),
    }
    if y >= 2022:
        h.add(_observed(date(y, 6, 19)))
    if y == 2018:
        h.add(date(2018, 12, 5))
    return h


def _context_date(context, trading_dates: list[date]) -> date | None:
    """Return the session being evaluated without reusing stale bars.

    If the engine supplies an as-of/today date it must be one of the available
    bar dates; otherwise a weekend/holiday invocation with a stale last bar
    should not create a fresh signal.  When no explicit date is supplied, fall
    back to the latest bar date for compatibility with simple daily backtests.
    """
    for name in ("as_of", "today"):
        value = getattr(context, name, None)
        if value is None:
            continue
        d = pd.Timestamp(value).tz_convert("America/New_York").date() if pd.Timestamp(value).tzinfo else pd.Timestamp(value).date()
        return d if d in set(trading_dates) else None
    return trading_dates[-1] if trading_dates else None


def _is_imminent_full_day_premarket_holiday(today: date) -> bool:
    holidays = _holiday_dates(today.year) | _holiday_dates(today.year + 1)
    return any(today + timedelta(days=delta) in holidays for delta in (1, 2, 3))


def generate_signals(context) -> dict[str, float]:
    symbols = list(context.symbols)
    weights = {s: 0.0 for s in symbols}
    prices = getattr(context, "prices", None)
    if prices is None or len(prices) == 0:
        return weights

    df = prices.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    trading_dates = sorted(set(df["timestamp"].dt.tz_convert("America/New_York").dt.date))
    today = _context_date(context, trading_dates)
    if today is None or not _is_imminent_full_day_premarket_holiday(today):
        return weights

    available = [s for s in UNIVERSE if s in symbols]
    if len(available) < 6:
        return weights
    w = 1.0 / len(available)
    for s in available:
        weights[s] = w
    return weights
