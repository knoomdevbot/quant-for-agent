"""AR-124 post-split effective-date liquidity/attention drift model.

QFA-compatible research model exposing generate_signals(context) -> dict[str, float].
The model is deliberately event-aware and timestamp-safe: it only acts when a
caller supplies split corporate-action metadata whose ex/process/effective date
is already in the observed price history, and it enters after that date. If no
corporate-action schedule is present, it returns zero weights safely.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import pandas as pd

SELECTED_UNIVERSE = (
    "AAON",
    "AIV",
    "AMZN",
    "ANET",
    "APG",
    "APH",
    "AVGO",
    "BEPC",
    "BKNG",
    "BN",
    "CELH",
    "CHDN",
)


@dataclass(frozen=True)
class Params:
    holding_days: int = 5
    gross_exposure: float = 1.0
    max_symbol_weight: float = 0.20
    min_history_days: int = 80


PARAMS = Params()


def _zero(symbols: list[str]) -> dict[str, float]:
    return {s: 0.0 for s in symbols}


def _event_date(event: dict[str, Any]) -> date | None:
    raw = event.get("ex_date") or event.get("process_date") or event.get("effective_date")
    if raw is None:
        return None
    try:
        ts = pd.Timestamp(raw)
        if pd.isna(ts):
            return None
        return ts.date()
    except Exception:
        return None


def _symbol(event: dict[str, Any]) -> str | None:
    value = event.get("symbol") or event.get("new_symbol") or event.get("old_symbol")
    return str(value).upper() if value else None


def _is_forward_split(event: dict[str, Any]) -> bool:
    typ = str(event.get("corporate_action_type") or event.get("type") or "").lower()
    if "reverse" in typ or "unit" in typ:
        return False
    if "forward" in typ or "split" in typ:
        try:
            return float(event.get("new_rate", 0)) > float(event.get("old_rate", 0))
        except Exception:
            return "forward" in typ
    return False


def _events_from_context(context: Any) -> list[dict[str, Any]]:
    events = getattr(context, "corporate_actions", None) or getattr(context, "events", None)
    if events is None:
        return []
    if isinstance(events, pd.DataFrame):
        return events.to_dict("records")
    if isinstance(events, dict):
        return list(events.get("forward_splits", [])) + list(events.get("splits", []))
    return [e for e in events if isinstance(e, dict)]


def generate_signals(context) -> dict[str, float]:
    """Return equal-weight long signals for active post-forward-split windows.

    Required context fields:
    - symbols: tradable output universe.
    - prices: long daily OHLCV DataFrame with timestamp/symbol/close.
    - corporate_actions/events: split records with symbol, ex/process/effective
      date, and split rates/type. If absent, returns all zeros.
    """

    output_symbols = list(getattr(context, "symbols", []) or [])
    if not output_symbols:
        return {}
    prices = getattr(context, "prices", pd.DataFrame())
    if prices is None or prices.empty:
        return _zero(output_symbols)

    df = prices[prices["symbol"].isin(SELECTED_UNIVERSE)].copy()
    if df.empty or "timestamp" not in df.columns:
        return _zero(output_symbols)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    close = df.pivot(index="timestamp", columns="symbol", values="close").sort_index().ffill()
    if len(close) < PARAMS.min_history_days:
        return _zero(output_symbols)

    asof = close.index[-1].date()
    active: list[str] = []
    for event in _events_from_context(context):
        symbol = _symbol(event)
        event_dt = _event_date(event)
        if symbol not in SELECTED_UNIVERSE or symbol not in output_symbols or symbol not in close.columns:
            continue
        if event_dt is None or not _is_forward_split(event):
            continue
        # Only trade after the event date; never on/before the ex/process/effective date.
        post_dates = [pd.Timestamp(ts).date() for ts in close.index if pd.Timestamp(ts).date() > event_dt]
        if not post_dates or asof < post_dates[0]:
            continue
        active_window = set(post_dates[: PARAMS.holding_days])
        if asof in active_window and pd.notna(close[symbol].iloc[-1]):
            active.append(symbol)

    if not active:
        return _zero(output_symbols)
    weight = min(PARAMS.max_symbol_weight, PARAMS.gross_exposure / len(active))
    return {s: (weight if s in active else 0.0) for s in output_symbols}
