"""AR-151 zero-weight source-gate artifact.

The labor-claims vintage/release source gate did not pass in bounded recovery, so
this model intentionally emits no target exposure.  It is kept qfa-compatible for
provenance and to prevent accidental live allocation from an unvalidated source.
"""

UNIVERSE = ["SPY", "QQQ", "IWM", "XLK", "XLF", "XLU", "XLP", "TLT", "IEF", "SHY", "HYG", "LQD", "GLD"]


def generate_signals(context):
    """Return zero target weights until a timestamp/vintage-safe claims source exists."""
    return {symbol: 0.0 for symbol in UNIVERSE}
