"""AR-127 NYSE holiday pre-close ETF drift / post-holiday normalization.

QFA-compatible research model exposing ``generate_signals(context)``.  The rule is
strictly calendar based: if the next NYSE trading session is the last session
before a full NYSE holiday or a deterministic early-close eve, allocate to a fixed
broad equity ETF basket for the pre-holiday sleeve; if the next trading session is
the first session after a full NYSE holiday, allocate to the same basket for the
post-holiday sleeve.  It uses qfa/Alpaca OHLCV only for symbol coverage/tradability
checks and never submits orders.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, timedelta

import pandas as pd

BROAD_EQUITY = ("SPY", "QQQ", "IWM", "DIA")
SECTOR_DIAGNOSTICS = ("XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY")
CONTROLS = ("TLT", "IEF", "SHY", "GLD")
CANDIDATE_POOL = BROAD_EQUITY + SECTOR_DIAGNOSTICS + CONTROLS


@dataclass(frozen=True)
class Params:
    min_history: int = 60
    gross: float = 1.0
    include_full_holiday_pre_sleeve: bool = True
    include_early_close_pre_sleeve: bool = True
    include_post_holiday_sleeve: bool = True


PARAMS = Params()


def _observed_fixed(d: date) -> date:
    if d.weekday() == 5:
        return d - timedelta(days=1)
    if d.weekday() == 6:
        return d + timedelta(days=1)
    return d


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    d = date(year, month, 1)
    return d + timedelta(days=((weekday - d.weekday()) % 7) + 7 * (n - 1))


def _last_weekday(year: int, month: int, weekday: int) -> date:
    d = date(year, month, calendar.monthrange(year, month)[1])
    return d - timedelta(days=(d.weekday() - weekday) % 7)


def _easter_sunday(year: int) -> date:
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
    month = (h + letter_l - 7 * m + 114) // 31
    day = ((h + letter_l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def nyse_full_holidays(year: int) -> set[date]:
    """Deterministic NYSE full-close holiday set for the modern ETF sample."""
    holidays = {
        _observed_fixed(date(year, 1, 1)),
        _nth_weekday(year, 1, 0, 3),
        _nth_weekday(year, 2, 0, 3),
        _easter_sunday(year) - timedelta(days=2),
        _last_weekday(year, 5, 0),
        _observed_fixed(date(year, 7, 4)),
        _nth_weekday(year, 9, 0, 1),
        _nth_weekday(year, 11, 3, 4),
        _observed_fixed(date(year, 12, 25)),
    }
    if year >= 2022:
        holidays.add(_observed_fixed(date(year, 6, 19)))
    return {d for d in holidays if d.year == year}


def nyse_early_closes(year: int) -> set[date]:
    """Rule-based regular NYSE early closes: day after Thanksgiving and Christmas Eve.

    Special one-off closures are deliberately excluded to avoid discretionary labels.
    """
    out = {_nth_weekday(year, 11, 3, 4) + timedelta(days=1)}
    christmas_eve = date(year, 12, 24)
    if christmas_eve.weekday() < 5 and christmas_eve not in nyse_full_holidays(year):
        out.add(christmas_eve)
    july3 = date(year, 7, 3)
    if july3.weekday() < 5 and date(year, 7, 4).weekday() in {1, 2, 3, 4, 5}:
        out.add(july3)
    return {d for d in out if d.weekday() < 5 and d not in nyse_full_holidays(year)}


def is_trading_day(d: date) -> bool:
    return d.weekday() < 5 and d not in (nyse_full_holidays(d.year) | nyse_full_holidays(d.year - 1) | nyse_full_holidays(d.year + 1))


def next_trading_day(d: date) -> date:
    d += timedelta(days=1)
    while not is_trading_day(d):
        d += timedelta(days=1)
    return d


def prev_trading_day(d: date) -> date:
    d -= timedelta(days=1)
    while not is_trading_day(d):
        d -= timedelta(days=1)
    return d


def session_label(d: date) -> str | None:
    """Classify a trading date as pre_full, pre_early, post_full, or None."""
    if not is_trading_day(d):
        return None
    nxt = d + timedelta(days=1)
    saw_holiday = False
    while nxt.weekday() >= 5 or nxt in nyse_full_holidays(nxt.year):
        if nxt in nyse_full_holidays(nxt.year):
            saw_holiday = True
        nxt += timedelta(days=1)
    if saw_holiday:
        return "pre_full"
    if d in nyse_early_closes(d.year):
        return "pre_early"
    prv = d - timedelta(days=1)
    saw_holiday = False
    while prv.weekday() >= 5 or prv in nyse_full_holidays(prv.year):
        if prv in nyse_full_holidays(prv.year):
            saw_holiday = True
        prv -= timedelta(days=1)
    if saw_holiday:
        return "post_full"
    return None


def _zero(symbols: list[str]) -> dict[str, float]:
    return {s: 0.0 for s in symbols}


def generate_signals(context) -> dict[str, float]:
    symbols = list(getattr(context, "symbols", []) or [])
    prices = getattr(context, "prices", pd.DataFrame())
    if prices.empty or not symbols:
        return _zero(symbols)
    df = prices[prices["symbol"].isin(BROAD_EQUITY)].copy()
    if df.empty:
        return _zero(symbols)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    close = df.pivot(index="timestamp", columns="symbol", values="close").sort_index().ffill()
    if len(close) < PARAMS.min_history:
        return _zero(symbols)
    asof_date = close.index.max().date()  # type: ignore[union-attr]
    target_date = next_trading_day(asof_date)
    label = session_label(target_date)
    active = (
        (label == "pre_full" and PARAMS.include_full_holiday_pre_sleeve)
        or (label == "pre_early" and PARAMS.include_early_close_pre_sleeve)
        or (label == "post_full" and PARAMS.include_post_holiday_sleeve)
    )
    if not active:
        return _zero(symbols)
    tradable = [s for s in BROAD_EQUITY if s in symbols and s in close.columns and pd.notna(close[s].iloc[-1])]
    if not tradable:
        return _zero(symbols)
    w = PARAMS.gross / len(tradable)
    return {s: (w if s in tradable else 0.0) for s in symbols}
