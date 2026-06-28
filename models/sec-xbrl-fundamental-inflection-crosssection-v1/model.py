"""AR-139 SEC XBRL fundamental inflection allocator (blocked/rejected preflight).

The issue requires timestamp-safe SEC 10-Q/10-K XBRL fundamentals. The public SEC
companyfacts endpoint available at research time is a current compiled view with
per-fact filing dates but not a historical as-of snapshot. Because restatements
and later filings can add/revise prior-period observations, the research artifact
is intentionally non-trading: it returns zero weights unless an external runtime
context explicitly supplies precomputed, point-in-time-safe signals.

No CSV, qfa daemon, or orders are used by this model.
"""
from __future__ import annotations

from typing import Any, Mapping


def _normalise(weights: Mapping[str, float]) -> dict[str, float]:
    cleaned = {str(k).upper(): float(v) for k, v in weights.items() if float(v) == float(v)}
    gross = sum(abs(v) for v in cleaned.values())
    if gross <= 0:
        return {k: 0.0 for k in cleaned}
    return {k: v / gross for k, v in cleaned.items()}


def generate_signals(context: Any) -> dict[str, float]:
    """Return portfolio weights.

    Runtime safety contract:
    - If ``context`` supplies ``metadata['ar139_pit_signals']`` (or an attribute
      with that name), those already point-in-time-safe signals are normalized.
    - Otherwise this blocked artifact emits zero weights for any symbols visible
      in the runtime context. It never downloads SEC data or reconstructs facts
      on the fly, because doing so from current companyfacts would risk hindsight.
    """
    meta = getattr(context, "metadata", None)
    if isinstance(meta, Mapping) and isinstance(meta.get("ar139_pit_signals"), Mapping):
        return _normalise(meta["ar139_pit_signals"])
    supplied = getattr(context, "ar139_pit_signals", None)
    if isinstance(supplied, Mapping):
        return _normalise(supplied)

    prices = getattr(context, "prices", None)
    if isinstance(prices, Mapping):
        return {str(k).upper(): 0.0 for k in prices.keys()}
    columns = getattr(prices, "columns", None)
    if columns is not None:
        return {str(k).upper(): 0.0 for k in columns}
    symbols = getattr(context, "symbols", None)
    if symbols is not None:
        return {str(k).upper(): 0.0 for k in symbols}
    return {}
