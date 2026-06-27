"""AR-014 event-drift proxy alpha for qfa.

This model is intentionally event-timed, not a continuation/refinement of AR-001
momentum. qfa/Alpaca in this repository exposes real OHLCV bars, but not true
fundamental earnings-calendar data, so the event definition is a documented
price/volume proxy: an abnormal overnight gap plus abnormal volume. Signals are
held for a fixed 20 trading-day post-event diffusion window with linear decay.
"""

from __future__ import annotations

import math

import pandas as pd

LOOKBACK_DAYS = 80
VOL_WINDOW = 20
HOLD_DAYS = 20
MIN_HISTORY = 45
MIN_ABS_GAP = 0.025
MIN_ABS_CLOSE_TO_CLOSE = 0.015
MIN_VOLUME_MULTIPLE = 1.35
MAX_ABS_WEIGHT = 0.25


def _last_event_score(symbol_frame: pd.DataFrame) -> float:
    """Return the decayed score from the most recent proxy event, or 0."""
    df = symbol_frame.sort_values("timestamp").tail(LOOKBACK_DAYS).copy()
    if len(df) < MIN_HISTORY:
        return 0.0

    df["prev_close"] = df["close"].shift(1)
    df["gap"] = df["open"] / df["prev_close"] - 1.0
    df["close_to_close"] = df["close"] / df["prev_close"] - 1.0
    df["avg_volume"] = df["volume"].shift(1).rolling(VOL_WINDOW).mean()
    df["volume_multiple"] = df["volume"] / df["avg_volume"]

    events = df[
        (df["prev_close"] > 0)
        & (df["avg_volume"] > 0)
        & (df["gap"].abs() >= MIN_ABS_GAP)
        & (df["close_to_close"].abs() >= MIN_ABS_CLOSE_TO_CLOSE)
        & (df["volume_multiple"] >= MIN_VOLUME_MULTIPLE)
    ]
    if events.empty:
        return 0.0

    event = events.iloc[-1]
    event_position = df.index.get_loc(event.name)
    days_since = len(df) - 1 - event_position
    if days_since < 0 or days_since > HOLD_DAYS:
        return 0.0

    direction = 1.0 if float(event["close_to_close"]) > 0 else -1.0
    event_strength = min(abs(float(event["gap"])) / MIN_ABS_GAP, 3.0)
    volume_strength = min(float(event["volume_multiple"]) / MIN_VOLUME_MULTIPLE, 3.0)
    decay = max(0.0, (HOLD_DAYS - days_since + 1) / HOLD_DAYS)
    score = direction * math.sqrt(event_strength * volume_strength) * decay
    return float(score) if math.isfinite(score) else 0.0


def generate_signals(context) -> dict[str, float]:
    """Generate target weights keyed by symbol for qfa AlphaContext."""
    prices = context.prices.copy()
    if prices.empty:
        return {symbol: 0.0 for symbol in context.symbols}

    raw_scores: dict[str, float] = {}
    for symbol in context.symbols:
        frame = prices[prices["symbol"] == symbol]
        raw_scores[symbol] = _last_event_score(frame) if not frame.empty else 0.0

    gross = sum(abs(value) for value in raw_scores.values())
    if gross <= 0:
        return {symbol: 0.0 for symbol in context.symbols}

    weights = {symbol: value / gross for symbol, value in raw_scores.items()}
    clipped = {symbol: max(min(weight, MAX_ABS_WEIGHT), -MAX_ABS_WEIGHT) for symbol, weight in weights.items()}
    clipped_gross = sum(abs(value) for value in clipped.values())
    if clipped_gross <= 0:
        return {symbol: 0.0 for symbol in context.symbols}
    return {symbol: value / clipped_gross for symbol, value in clipped.items()}
