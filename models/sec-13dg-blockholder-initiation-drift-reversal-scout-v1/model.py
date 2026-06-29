"""SEC 13D/13G blockholder initiation drift/reversal feasibility scout.

AR-146 is intentionally inert: the bounded recovery run only checked compact SEC
submissions metadata counts. It did not build a timestamp-safe parsed event table
or run a qfa/Alpaca performance backtest, so no trading signal is enabled.
"""


def generate_signals(context):
    """Return no signals for the feasibility-only rejected scout.

    Args:
        context: Runtime context supplied by quant-for-agent.

    Returns:
        An empty dict because AR-146 did not pass the source/event-table gate.
    """
    _ = context
    return {}
