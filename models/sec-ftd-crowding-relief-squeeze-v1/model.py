"""AR-138 SEC FTD crowding relief/squeeze allocator.

Runtime-safe qfa model wrapper. The research evaluation used an offline,
timestamp-lagged SEC FTD event table plus real Alpaca/qfa daily bars. Because the
external FTD event table is not bundled into the qfa runtime contract, this model
returns zero weights unless precomputed event weights are supplied in
context.metadata['ar138_event_weights'] for context.as_of.
"""

from __future__ import annotations


def generate_signals(context):
    """Return precomputed AR-138 weights when supplied, otherwise stay in cash."""
    metadata = getattr(context, "metadata", {}) or {}
    as_of = str(getattr(context, "as_of", ""))[:10]
    event_weights = metadata.get("ar138_event_weights", {})
    weights = event_weights.get(as_of, {}) if isinstance(event_weights, dict) else {}
    symbols = set(getattr(context, "symbols", []) or [])
    return {symbol: float(weight) for symbol, weight in weights.items() if symbol in symbols}
