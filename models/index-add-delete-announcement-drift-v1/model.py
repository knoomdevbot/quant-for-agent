"""AR-141 placeholder model.

This alpha is on hold because the prerequisite timestamp-safe index-membership
announcement event source did not pass the source gate. Do not trade or backtest
with inferred/index-calendar proxies.
"""

MODEL_NAME = "index-add-delete-announcement-drift-v1"
DECISION = "hold"
HOLD_REASON = (
    "No reproducible timestamp-safe public addition/deletion event source with "
    ">=150 liquid common-stock events was available in the repository or proven "
    "from public web endpoints during the source-gate scout."
)


def generate_signals(*args, **kwargs):
    """Refuse to fabricate signals until the external event-source gate passes."""
    raise RuntimeError(
        "AR-141 is on hold: timestamp-safe public index addition/deletion "
        "announcement records are required before signal generation."
    )
