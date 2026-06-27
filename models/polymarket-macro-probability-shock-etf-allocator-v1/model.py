"""AR-091 Polymarket macro probability shock ETF allocator (blocked artifact).

The research issue requires reproducible, point-in-time prediction-market
probability histories.  During this investigation the public Polymarket/Gamma
endpoints were reachable for current market snapshots and token-level price
history, but not sufficient to commit a reproducible point-in-time macro market
selection/history pipeline without retaining raw external data or introducing
selection/lookahead bias.  Therefore this qfa-compatible model intentionally
contains no fabricated proxy signal and only returns a cash-like fallback.
"""
from __future__ import annotations

from typing import Any

UNIVERSE = [
    "SPY", "QQQ", "IWM", "TLT", "IEF", "SHY", "GLD", "HYG", "LQD",
    "XLE", "XLU", "XLV", "XLF", "KRE", "ITA", "XLI", "XLP", "XLY",
    "FXI", "EEM", "USO", "UUP",
]
FALLBACK_SYMBOL = "SHY"


def generate_signals(context: Any) -> dict[str, float]:
    """Return defensive fallback weights only.

    This is a blocked research artifact, not an active alpha.  It avoids using
    unavailable/non-reproducible prediction-market data and does not place
    orders.  If the requested universe lacks SHY, the function returns all-zero
    weights rather than substituting an unresearched asset.
    """
    symbols = list(getattr(context, "symbols", UNIVERSE) or UNIVERSE)
    weights = {symbol: 0.0 for symbol in symbols}
    if FALLBACK_SYMBOL in weights:
        weights[FALLBACK_SYMBOL] = 1.0
    return weights
