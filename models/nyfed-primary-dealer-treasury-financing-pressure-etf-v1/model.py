"""AR-149 source-gated scaffold.

NY Fed Primary Dealer Statistics timing/revision gate did not pass, so this
model intentionally emits no active duration ETF positions.  It is kept only
as a durable research artifact for the scout decision.
"""

from __future__ import annotations

ALPHA_ID = "AR-149"
SELECTED_UNIVERSE = ("TLT", "IEF", "IEI", "SHY", "GOVT")


def generate_signals(context):
    """Return flat target weights while AR-149 is source-vintage gated.

    The research gate found documented as-of/publication timing, but no
    machine-readable point-in-time vintage or revision policy adequate for a
    live signal using historical dealer statistics.  To avoid accidental use of
    revised history, the production surface is a no-op.
    """

    return {symbol: 0.0 for symbol in SELECTED_UNIVERSE}
