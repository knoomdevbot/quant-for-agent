"""AR-141 index addition/deletion announcement drift research stub.

The timestamp-safe public announcement source gate failed, so this model is
intentionally inactive. It exposes the qfa-compatible generate_signals(context)
entry point while returning no target weights/signals.
"""

MODEL_NAME = "index-add-delete-announcement-drift-v1"
STATUS = "rejected_blocked_source_gate"


def generate_signals(context):
    """Return no signals because AR-141 failed its event-source gate.

    Parameters
    ----------
    context : object
        qfa research context; unused for this blocked artifact.
    """
    return {}
