from __future__ import annotations

from datetime import date, timedelta

# AR-127 durable qfa model. No file/data access; deterministic public-calendar rules only.
NO_CSV_USED = True
NO_DATA_CSV_ARGUMENT_USED = True
NO_DAEMON = True
NO_ORDERS = True
RAW_DAILY_PATHS_RETAINED = False

RISK_ON = [
    "SPY", "QQQ", "IWM", "MDY", "EFA", "EEM", "XLK", "XLF", "XLY", "XLI",
    "HYG", "LQD", "DBC", "USO",
]
DEFENSIVE = ["TLT", "IEF", "SHY", "GLD", "UUP", "XLU", "XLP"]


def _observed_fixed(year: int, month: int, day: int) -> date:
    d = date(year, month, day)
    if d.weekday() == 5:  # Saturday observed Friday
        return d - timedelta(days=1)
    if d.weekday() == 6:  # Sunday observed Monday
        return d + timedelta(days=1)
    return d


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    d = date(year, month, 1)
    while d.weekday() != weekday:
        d += timedelta(days=1)
    return d + timedelta(days=7 * (n - 1))


def _last_weekday(year: int, month: int, weekday: int) -> date:
    d = date(year + (month == 12), 1 if month == 12 else month + 1, 1) - timedelta(days=1)
    while d.weekday() != weekday:
        d -= timedelta(days=1)
    return d


def _easter(year: int) -> date:
    # Anonymous Gregorian algorithm.
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
    offset = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * offset) // 451
    month = (h + offset - 7 * m + 114) // 31
    day = ((h + offset - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def _nyse_holidays(year: int) -> set[date]:
    h = {
        _observed_fixed(year, 1, 1),
        _nth_weekday(year, 1, 0, 3),       # MLK
        _nth_weekday(year, 2, 0, 3),       # Presidents
        _easter(year) - timedelta(days=2), # Good Friday
        _last_weekday(year, 5, 0),         # Memorial
        _observed_fixed(year, 7, 4),
        _nth_weekday(year, 9, 0, 1),       # Labor
        _nth_weekday(year, 11, 3, 4),      # Thanksgiving
        _observed_fixed(year, 12, 25),
    }
    if year >= 2022:
        h.add(_observed_fixed(year, 6, 19))
    # One-off full NYSE closures present in the research sample.
    h |= {date(2018, 12, 5), date(2025, 1, 9)}
    return h


def _is_session(d: date) -> bool:
    return d.weekday() < 5 and d not in _nyse_holidays(d.year)


def _next_session(d: date) -> date:
    x = d + timedelta(days=1)
    while not _is_session(x):
        x += timedelta(days=1)
    return x


def _has_weekday_closure_between(a: date, b: date) -> bool:
    x = a + timedelta(days=1)
    while x < b:
        if x.weekday() < 5:
            return True
        x += timedelta(days=1)
    return False


def _as_date(ts) -> date:
    if hasattr(ts, "date"):
        return ts.date()
    return date.fromisoformat(str(ts)[:10])


def generate_signals(context):
    """Return qfa weights for pre-holiday risk-on and post-holiday defensive timing.

    Signal timing matches qfa next-bar execution: weights produced at an as_of close are
    held over the next daily close-to-close interval.
    """
    asof = _as_date(context.as_of)
    if not _is_session(asof):
        return {}
    next_s = _next_session(asof)
    next_next_s = _next_session(next_s)
    symbols = set(getattr(context, "symbols", []) or [])

    if _has_weekday_closure_between(next_s, next_next_s):
        sleeve = [s for s in RISK_ON if s in symbols]
    elif _has_weekday_closure_between(asof, next_s):
        sleeve = [s for s in DEFENSIVE if s in symbols]
    else:
        sleeve = []
    if not sleeve:
        return {}
    w = 1.0 / len(sleeve)
    return {s: w for s in sleeve}
