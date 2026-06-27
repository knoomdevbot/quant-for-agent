"""AR-125 common-stock ex-dividend post-date rebound/drift model.

QFA-compatible research model exposing generate_signals(context) -> dict[str, float].
The model is timestamp-safe by construction: it only enters after the first
observed daily bar strictly after max(ex_date, process_date) for supplied Alpaca
cash-dividend corporate-action records. If no suitable dividend events are
supplied, it returns zero weights.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, cast

import pandas as pd


@dataclass(frozen=True)
class Params:
    holding_days: int = 5
    gross_exposure: float = 1.0
    max_symbol_weight: float = 0.02
    min_history_days: int = 40
    min_price: float = 10.0
    min_pre60_dollar_volume: float = 1_000_000.0


PARAMS = Params()


def _zero(symbols: list[str]) -> dict[str, float]:
    return {s: 0.0 for s in symbols}


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    try:
        ts = pd.Timestamp(value)
        if pd.isna(ts):
            return None
        return cast(date, ts.date())
    except Exception:
        return None


def _decision_date(event: dict[str, Any]) -> date | None:
    dates = [_parse_date(event.get("ex_date")), _parse_date(event.get("process_date"))]
    dates = [d for d in dates if d is not None]
    return max(dates) if dates else None


def _events_from_context(context: Any) -> list[dict[str, Any]]:
    events = getattr(context, "corporate_actions", None) or getattr(context, "events", None)
    if events is None:
        return []
    if isinstance(events, pd.DataFrame):
        return events.to_dict("records")
    if isinstance(events, dict):
        return list(events.get("cash_dividends", [])) + list(events.get("dividends", []))
    return [e for e in events if isinstance(e, dict)]


def _is_primary_cash_dividend(event: dict[str, Any]) -> bool:
    typ = str(event.get("corporate_action_type") or event.get("type") or "").lower()
    if typ and "cash" not in typ and "dividend" not in typ:
        return False
    if bool(event.get("special")) or bool(event.get("foreign")):
        return False
    return event.get("symbol") is not None and event.get("rate") is not None


def generate_signals(context) -> dict[str, float]:
    """Return equal-weight long signals for active post-dividend windows.

    Required context fields:
    - symbols: tradable output universe.
    - prices: long daily OHLCV DataFrame with timestamp/symbol/close/volume.
    - corporate_actions/events: cash-dividend records with symbol, ex_date,
      process_date, rate, special, and foreign. If absent, all weights are zero.
    """

    output_symbols = list(getattr(context, "symbols", []) or [])
    if not output_symbols:
        return {}
    prices = getattr(context, "prices", pd.DataFrame())
    if prices is None or prices.empty or "timestamp" not in prices.columns:
        return _zero(output_symbols)

    df = prices[prices["symbol"].isin(output_symbols)].copy()
    if df.empty:
        return _zero(output_symbols)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df.sort_values(by=["symbol", "timestamp"])
    asof = df["timestamp"].max().date()
    active: list[str] = []

    events = _events_from_context(context)
    if not events:
        return _zero(output_symbols)

    for event in events:
        if not _is_primary_cash_dividend(event):
            continue
        symbol = str(event.get("symbol", "")).upper()
        if symbol not in output_symbols:
            continue
        decision = _decision_date(event)
        if decision is None:
            continue
        g = df[df["symbol"] == symbol].reset_index(drop=True)
        if len(g) < PARAMS.min_history_days + PARAMS.holding_days + 1:
            continue
        post_idx = [i for i, ts in enumerate(g["timestamp"]) if pd.Timestamp(ts).date() > decision]
        if not post_idx:
            continue
        entry_i = post_idx[0]
        post_window = {cast(date, pd.Timestamp(g.iloc[i]["timestamp"]).date()) for i in post_idx[: PARAMS.holding_days]}
        if asof not in post_window:
            continue
        pre = g.iloc[max(0, entry_i - 61) : max(0, entry_i - 1)]
        if len(pre) < PARAMS.min_history_days:
            continue
        entry_close = float(g.iloc[entry_i]["close"])
        pre_dv = float((pre["close"] * pre["volume"]).median()) if "volume" in pre else 0.0
        if entry_close < PARAMS.min_price or pre_dv < PARAMS.min_pre60_dollar_volume:
            continue
        active.append(symbol)

    if not active:
        return _zero(output_symbols)
    weight = min(PARAMS.max_symbol_weight, PARAMS.gross_exposure / len(active))
    return {s: (weight if s in active else 0.0) for s in output_symbols}
