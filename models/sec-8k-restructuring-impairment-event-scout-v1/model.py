"""AR-146 SEC 8-K event scout placeholder.

Held before performance because the timestamp-safe SEC Item 2.05/2.06
event-source gate was not verified.
"""


def generate_signals(context):
    """Return no positions while the event-source dependency remains on hold."""
    return {}
