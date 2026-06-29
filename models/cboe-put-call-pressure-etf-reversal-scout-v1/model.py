"""AR-148 CBOE put/call pressure ETF reversal scout.

The research run rejected this alpha on real data.  The production-facing
function therefore emits a neutral allocation rather than attempting to fetch
CBOE web data at signal time.
"""

from __future__ import annotations

from typing import Any

SELECTED_UNIVERSE = (
    "SPY",
    "QQQ",
    "IWM",
    "DIA",
    "XLK",
    "XLF",
    "XLE",
    "XLU",
    "TLT",
    "IEF",
    "SHY",
)


def generate_signals(context: Any) -> dict[str, float]:
    """Return neutral weights for the rejected AR-148 scout.

    The feasibility source gate passed for timestamp-safe historical research,
    but performance and random-window robustness gates failed after costs.  To
    avoid live dependency on CBOE page scraping and to prevent deploying a
    rejected signal, this callable intentionally returns zero target weights for
    the selected ETF universe.
    """

    symbols = getattr(context, "symbols", None) or SELECTED_UNIVERSE
    return {str(symbol): 0.0 for symbol in symbols if str(symbol) in SELECTED_UNIVERSE}
