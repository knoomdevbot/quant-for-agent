"""AR-006 turn-of-month seasonality alpha for broad liquid ETFs.

QFA contract: expose generate_signals(context) -> dict[str, float].
The model is research-only, data-source agnostic, and reads only context prices/as_of.

Signal definition:
- hold a diversified long basket during the turn-of-month window;
- window is the final 3 business days of each calendar month plus the first
  3 business days of the next month, evaluated at the close of context.as_of
  for the next qfa bar return;
- stay flat outside the window;
- equal-weight active symbols and cap single-name weight before qfa normalization.
"""

from __future__ import annotations

import pandas as pd
from pandas.tseries.offsets import BDay, BMonthEnd


DEFAULT_PARAMS = {
    "pre_month_end_business_days": 3,
    "post_month_start_business_days": 3,
    "max_abs_weight": 0.25,
    "min_observations": 2,
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
        return pd.Timestamp(as_of).tz_convert("UTC") if pd.Timestamp(as_of).tzinfo else pd.Timestamp(as_of, tz="UTC")

    prices = getattr(context, "prices", pd.DataFrame())
    if prices.empty or "timestamp" not in prices:
        return None
    return pd.to_datetime(prices["timestamp"], utc=True).max()


def _is_turn_of_month(as_of: pd.Timestamp, pre_days: int, post_days: int) -> bool:
    """Return True inside the no-lookahead calendar turn-of-month window."""
    day = as_of.tz_convert("UTC").normalize().tz_localize(None)

    month_start = day.replace(day=1)
    month_end = month_start + BMonthEnd(0)
    pre_start = month_end - BDay(max(pre_days - 1, 0))
    post_end = month_start + BDay(max(post_days - 1, 0))
    return bool(day >= pre_start or day <= post_end)


def _active_symbols(context, symbols: list[str], min_observations: int) -> list[str]:
    prices = getattr(context, "prices", pd.DataFrame())
    if prices.empty or "symbol" not in prices or "close" not in prices:
        return symbols
    available = []
    for symbol in symbols:
        series = prices.loc[prices["symbol"] == symbol, "close"].dropna()
        if len(series) >= min_observations:
            available.append(symbol)
    return available


def generate_signals(context):
    """Return turn-of-month target weights for context.symbols."""
    symbols = list(getattr(context, "symbols", []) or [])
    if not symbols:
        return {}

    params = _params(context)
    as_of = _as_timestamp(context)
    if as_of is None:
        return {symbol: 0.0 for symbol in symbols}

    if not _is_turn_of_month(
        as_of,
        int(params["pre_month_end_business_days"]),
        int(params["post_month_start_business_days"]),
    ):
        return {symbol: 0.0 for symbol in symbols}

    active = _active_symbols(context, symbols, int(params["min_observations"]))
    if not active:
        return {symbol: 0.0 for symbol in symbols}

    equal_weight = 1.0 / len(active)
    capped_weight = min(equal_weight, float(params["max_abs_weight"]))
    return {symbol: (capped_weight if symbol in active else 0.0) for symbol in symbols}
