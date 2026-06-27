"""AR-120 timestamp-safe ETF distribution/ex-date allocator (blocked stub).

The research issue requires timestamp-safe ETF distribution/corporate-action
knowledge before a trading decision. Alpaca cash-dividend records were available
for the candidate ETFs, but the observed alpaca-py response did not include an
announcement/as-of/knowledge timestamp. To avoid look-ahead bias, this model is
intentionally inert and returns cash/zero target weights until a timestamp-safe
event feed is integrated.

QFA contract: expose generate_signals(context) -> dict[symbol, weight].
No CSV, no daemon, no orders.
"""
from __future__ import annotations

UNIVERSE = [
    "HYG", "LQD", "SHY", "IEF", "TLT", "GOVT", "TIP", "EMB", "MUB",
    "VCIT", "VCSH", "BND", "AGG", "XLU", "XLP", "XLV", "VNQ", "XLRE",
]


def generate_signals(context) -> dict[str, float]:
    """Return zero/cash weights because AR-120 is blocked for timestamp safety."""
    symbols = list(getattr(context, "symbols", []) or [])
    return {symbol: 0.0 for symbol in symbols}
