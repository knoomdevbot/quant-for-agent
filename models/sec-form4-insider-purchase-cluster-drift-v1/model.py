"""AR-134 recovery artifact: SEC Form 4 insider-purchase cluster drift.

This model is intentionally inert because the point-in-time SEC Form 4 event
source was not constructed within the bounded recovery run. It exposes the qfa
contract function but returns no signals rather than fabricating an evaluated
alpha or trading on incomplete event data.

No qfa daemon, orders, CSV market data, or --data-csv inputs are used here.
"""
from __future__ import annotations

from typing import Any


def generate_signals(context: Any) -> dict[str, float]:
    """Return no positions until timestamp-safe Form 4 event table exists.

    Required missing prerequisite: a validated PIT table of SEC Form 4 XML
    filings with acceptance timestamps, issuer ticker mapping, officer/director
    role flags, non-derivative open-market purchase code P / acquisition A,
    distinct insider clustering, and qfa/Alpaca daily bar availability.
    """
    return {}
