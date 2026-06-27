"""AR-130 scheduled FOMC decision-day rate-sensitive ETF drift/fade model.

QFA contract: expose generate_signals(context) -> dict[str, float].

This model is intentionally simple and timestamp-safe: when context.as_of (or the
latest timestamp in context.prices) is a hardcoded public scheduled FOMC decision
date, it returns equal-weight long exposure to the fixed pre-review ETF basket;
otherwise it stays flat. It does not use realized macro surprises, intraday data,
CSV input, daemon state, or order placement.
"""

from __future__ import annotations

import pandas as pd

SELECTED_SYMBOLS = ["TLT", "IEF", "SHY", "LQD", "HYG", "GLD", "SPY", "QQQ", "XLF", "XLRE"]
MAX_GROSS_EXPOSURE = 1.0

SCHEDULED_FOMC_DECISION_DATES = {
    "2016-01-27", "2016-03-16", "2016-04-27", "2016-06-15", "2016-07-27", "2016-09-21", "2016-11-02", "2016-12-14",
    "2017-02-01", "2017-03-15", "2017-05-03", "2017-06-14", "2017-07-26", "2017-09-20", "2017-11-01", "2017-12-13",
    "2018-01-31", "2018-03-21", "2018-05-02", "2018-06-13", "2018-08-01", "2018-09-26", "2018-11-08", "2018-12-19",
    "2019-01-30", "2019-03-20", "2019-05-01", "2019-06-19", "2019-07-31", "2019-09-18", "2019-10-30", "2019-12-11",
    "2020-01-29", "2020-04-29", "2020-06-10", "2020-07-29", "2020-09-16", "2020-11-05", "2020-12-16",
    "2021-01-27", "2021-03-17", "2021-04-28", "2021-06-16", "2021-07-28", "2021-09-22", "2021-11-03", "2021-12-15",
    "2022-01-26", "2022-03-16", "2022-05-04", "2022-06-15", "2022-07-27", "2022-09-21", "2022-11-02", "2022-12-14",
    "2023-02-01", "2023-03-22", "2023-05-03", "2023-06-14", "2023-07-26", "2023-09-20", "2023-11-01", "2023-12-13",
    "2024-01-31", "2024-03-20", "2024-05-01", "2024-06-12", "2024-07-31", "2024-09-18", "2024-11-07", "2024-12-18",
    "2025-01-29", "2025-03-19", "2025-05-07", "2025-06-18", "2025-07-30", "2025-09-17", "2025-10-29", "2025-12-10",
    "2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17", "2026-07-29", "2026-09-16", "2026-10-28", "2026-12-09",
}


def _as_of_date(context) -> str | None:
    as_of = getattr(context, "as_of", None)
    if as_of is not None:
        return str(pd.Timestamp(as_of).date())
    prices = getattr(context, "prices", None)
    if prices is None or getattr(prices, "empty", True) or "timestamp" not in prices:
        return None
    return str(pd.to_datetime(prices["timestamp"], utc=True).max().date())


def generate_signals(context):
    """Return target weights: equal-weight long basket on scheduled FOMC days, flat otherwise."""
    symbols = list(getattr(context, "symbols", []) or SELECTED_SYMBOLS)
    weights = {symbol: 0.0 for symbol in symbols}
    as_of = _as_of_date(context)
    if as_of not in SCHEDULED_FOMC_DECISION_DATES:
        return weights
    active = [symbol for symbol in SELECTED_SYMBOLS if symbol in symbols]
    if not active:
        return weights
    weight = MAX_GROSS_EXPOSURE / len(active)
    for symbol in active:
        weights[symbol] = weight
    return weights
