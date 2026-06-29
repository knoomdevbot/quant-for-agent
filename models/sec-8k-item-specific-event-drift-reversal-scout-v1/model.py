"""SEC 8-K item-specific event drift/reversal feasibility scout.

This model is intentionally inert for AR-145: the bounded recovery run only
verified that SEC submissions metadata exposes timestamped Item 2.02 8-K event
fields for a small deterministic issuer sample. No performance signal was
accepted, and no live trading should be generated from this scout.
"""


def generate_signals(context):
    """Return no orders/signals for the feasibility-only rejected scout.

    Args:
        context: Runtime context supplied by quant-for-agent.

    Returns:
        An empty dict because AR-145 did not advance past feasibility scouting.
    """
    _ = context
    return {}
