"""AR-096 mega-cap analyst-revision dispersion drift allocator.

This alpha is intentionally blocked/flat in this repository version.

The stated mechanism requires durable point-in-time analyst revision breadth and
estimate-dispersion history. qfa/Alpaca available here exposes real OHLCV bars
through AlpacaGateway.get_bars, but no analyst-estimate, revision, dispersion,
or earnings-calendar feed. Rather than fabricate fundamental data or relabel an
OHLCV proxy as analyst revisions, generate_signals returns flat weights.

QFA contract: expose generate_signals(context) -> dict[str, float].
Research-only; no orders, no daemon behavior, no CSV dependency.
"""
from __future__ import annotations

UNIVERSE = ("AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "AVGO", "TSLA", "JPM", "LLY")


def _symbols_from_context(context) -> list[str]:
    symbols = getattr(context, "symbols", None)
    if symbols:
        return [str(s).upper() for s in symbols]
    prices = getattr(context, "prices", None)
    if prices is not None and hasattr(prices, "columns") and "symbol" in prices.columns:
        return sorted({str(s).upper() for s in prices["symbol"].dropna().unique()})
    return list(UNIVERSE)


def generate_signals(context) -> dict[str, float]:
    """Return flat weights because required PIT analyst-revision data is absent."""
    return {symbol: 0.0 for symbol in _symbols_from_context(context)}
