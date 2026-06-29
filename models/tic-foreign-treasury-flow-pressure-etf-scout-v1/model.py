"""AR-150 TIC foreign Treasury-flow pressure ETF scout.

This rejected source-gated scout is kept as a qfa-compatible artifact. The
research evaluation tested a release-vintage TIC pressure allocator and failed
post-cost random-window/control gates. To avoid accidental use, the durable
model emits cash/zero weights by default.
"""

UNIVERSE = ["TLT", "IEF", "SHY", "GOVT", "UUP", "GLD"]


def generate_signals(context):
    """Return zero weights for the rejected AR-150 scout.

    The completed evaluation is stored under evaluations/latest.json. This
    implementation intentionally avoids embedding parsed TIC release data or
    raw market data in source control.
    """
    symbols = getattr(context, "symbols", None) or UNIVERSE
    return {symbol: 0.0 for symbol in symbols}
