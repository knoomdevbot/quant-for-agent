"""AR-140 FINRA short-sale volume pressure reversal.

Runtime-safe qfa model wrapper. The research evaluation attempted to construct a
timestamp-lagged FINRA Reg SHO event table with real Alpaca/qfa bars. The final
candidate failed universe/event gates, so the default runtime model stays in cash
unless precomputed FINRA event weights are supplied in context metadata.
"""

from __future__ import annotations


def generate_signals(context):
    """Return precomputed AR-140 weights when supplied, otherwise stay in cash."""
    metadata = getattr(context, "metadata", {}) or {}
    as_of = str(getattr(context, "as_of", ""))[:10]
    event_weights = metadata.get("ar140_event_weights", {})
    weights = event_weights.get(as_of, {}) if isinstance(event_weights, dict) else {}
    symbols = set(getattr(context, "symbols", []) or [])
    return {symbol: float(weight) for symbol, weight in weights.items() if symbol in symbols}
