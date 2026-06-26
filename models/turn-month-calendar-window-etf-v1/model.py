"""AR-021 exchange-calendar-aware turn-of-month ETF seasonality alpha.

QFA contract: expose generate_signals(context) -> dict[str, float].

Signal definition:
- infer valid exchange sessions from the real Alpaca/qfa price timestamps already
  present in context (no synthetic weekday calendar and no CSV data);
- hold a diversified long basket during the final N observed sessions of each
  calendar month plus the first M observed sessions of each month;
- stay flat outside the window;
- equal-weight active symbols and cap single-symbol pre-normalization weights.

The default window (1 pre-month-end session + 4 post-month-start sessions) is a
small, prespecified refinement of AR-006 intended to reduce holiday/calendar
misclassification and trading days versus the parent's 3+3 business-day rule.
"""

from __future__ import annotations

import pandas as pd


DEFAULT_PARAMS = {
    "pre_month_end_sessions": 1,
    "post_month_start_sessions": 4,
    "max_abs_weight": 0.25,
    "min_observations": 20,
}


def _params(context) -> dict:
    metadata = getattr(context, "metadata", {}) or {}
    provided = metadata.get("params", {}) if isinstance(metadata, dict) else {}
    params = DEFAULT_PARAMS.copy()
    params.update({k: provided[k] for k in params.keys() & provided.keys()})
    return params


def _as_timestamp(context) -> pd.Timestamp | None:
    as_of = getattr(context, "as_of", None)
    if as_of is not None:
        ts = pd.Timestamp(as_of)
        return ts.tz_convert("UTC") if ts.tzinfo else ts.tz_localize("UTC")

    prices = getattr(context, "prices", pd.DataFrame())
    if prices.empty or "timestamp" not in prices:
        return None
    return pd.to_datetime(prices["timestamp"], utc=True).max()


def _observed_sessions(prices: pd.DataFrame) -> list[pd.Timestamp]:
    if prices.empty or "timestamp" not in prices:
        return []
    stamps = pd.to_datetime(prices["timestamp"], utc=True, errors="coerce").dropna()
    if stamps.empty:
        return []
    # qfa daily bars arrive with exchange bar timestamps; normalize to UTC
    # calendar date and deduplicate. This makes the window aware of actual
    # observed market sessions/holidays in the Alpaca data feed.
    dates = stamps.dt.tz_convert("UTC").dt.normalize().drop_duplicates().sort_values()
    return list(dates)


def _is_turn_window(as_of: pd.Timestamp, prices: pd.DataFrame, pre_sessions: int, post_sessions: int) -> bool:
    sessions = _observed_sessions(prices)
    if not sessions:
        return False

    day = as_of.tz_convert("UTC").normalize()
    if day not in set(sessions):
        return False

    month_sessions = [session for session in sessions if session.year == day.year and session.month == day.month]
    if not month_sessions:
        return False

    first_sessions = set(month_sessions[: max(int(post_sessions), 0)])
    last_sessions = set(month_sessions[-max(int(pre_sessions), 0) :]) if int(pre_sessions) > 0 else set()
    return day in first_sessions or day in last_sessions


def _active_symbols(context, symbols: list[str], min_observations: int) -> list[str]:
    prices = getattr(context, "prices", pd.DataFrame())
    if prices.empty or "symbol" not in prices or "close" not in prices:
        return symbols
    active = []
    for symbol in symbols:
        series = prices.loc[prices["symbol"] == symbol, "close"].dropna()
        if len(series) >= int(min_observations):
            active.append(symbol)
    return active


def generate_signals(context):
    """Return target weights for qfa's next-bar backtest step."""
    symbols = list(getattr(context, "symbols", []) or [])
    if not symbols:
        return {}

    prices = getattr(context, "prices", pd.DataFrame())
    params = _params(context)
    as_of = _as_timestamp(context)
    if as_of is None or prices.empty:
        return {symbol: 0.0 for symbol in symbols}

    if not _is_turn_window(
        as_of,
        prices,
        int(params["pre_month_end_sessions"]),
        int(params["post_month_start_sessions"]),
    ):
        return {symbol: 0.0 for symbol in symbols}

    active = _active_symbols(context, symbols, int(params["min_observations"]))
    if not active:
        return {symbol: 0.0 for symbol in symbols}

    equal_weight = 1.0 / len(active)
    capped_weight = min(equal_weight, float(params["max_abs_weight"]))
    return {symbol: (capped_weight if symbol in active else 0.0) for symbol in symbols}
