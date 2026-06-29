"""AR-145 SEC 8-K item-specific event drift/reversal scout.

This is intentionally cash-only until a timestamp-safe, point-in-time 8-K
item event table is implemented and passes feasibility gates.  The bounded
recovery run found SEC submissions metadata is accessible and item tagged, but
did not establish the required broad liquid Item 2.02 event table.
"""

from __future__ import annotations

from typing import Any


def generate_signals(context: Any) -> dict[str, float]:
    """Return no positions until event-table feasibility is resolved.

    A future non-cash version must only use EDGAR acceptance timestamps with a
    conservative post-acceptance/next-session lag, point-in-time ticker mapping,
    and liquid common-stock market-data coverage.  No fallback calendar-only or
    current-only ticker mapping signal is allowed here.
    """

    return {}
