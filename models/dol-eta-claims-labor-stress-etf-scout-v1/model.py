"""AR-151 source-gated scaffold.

The DOL/ETA unemployment-claims labor-stress scout did not pass the bounded
source/vintage gate.  It intentionally emits flat ETF weights so no live or
historical process can accidentally trade from revised claims history.
"""

from __future__ import annotations

ALPHA_ID = "AR-151"
SELECTED_UNIVERSE = (
    "SPY",
    "QQQ",
    "IWM",
    "XLK",
    "XLF",
    "XLU",
    "XLP",
    "TLT",
    "IEF",
    "SHY",
    "HYG",
    "LQD",
    "GLD",
)


def generate_signals(context):
    """Return flat target weights while AR-151 is source-vintage rejected.

    The bounded recovery checked official DOL/ETA pages and short-timeout FRED /
    ALFRED access.  It could not prove a compact, machine-readable point-in-time
    path that maps each historical claims observation to the public release date
    and vintage/revision state required by the falsifier.  Performance is
    therefore intentionally not evaluated and the production surface is a no-op.
    """

    return {symbol: 0.0 for symbol in SELECTED_UNIVERSE}
