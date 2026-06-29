"""AR-141 blocked research stub: index addition/deletion announcement drift.

The event-source gate did not pass, so this model intentionally emits no
positions. It remains importable for qfa research tooling and documents the
required timestamp-safe event-data dependency.
"""

from __future__ import annotations

from typing import Any


MODEL_NAME = "index-add-delete-announcement-drift-v1"
STATUS = "blocked_event_source"


def generate_signals(context: Any) -> dict[str, float]:
    """Return no target weights because timestamp-safe event data is absent.

    AR-141 required at least 150 reproducible public index addition/deletion
    announcement records before performance scoring. The source scout found
    effective-date constituent-change tables but not a durable announcement-date
    event table with enough breadth, so trading is disabled.
    """

    _ = context
    return {}
