"""AR-024 post-earnings information-diffusion proxy alpha for qfa.

qfa/Alpaca in this repository provides real OHLCV bars but not a dependable
fundamental earnings-calendar feed. This model therefore uses a documented
post-earnings-like price/volume event proxy and does not fabricate earnings
announcements.

Mechanism: a large close-to-close information shock with abnormal volume,
abnormal intraday range, and strong close location is treated as a delayed
information-diffusion event. The trigger intentionally excludes overnight gap as
a requirement and uses same-day close-to-close/intraday-volume evidence, so it is
not an overnight-gap reversal refinement or direct inversion. Signals begin only
after the event day and decay over a short 8-trading-day continuation window.
"""

from __future__ import annotations

import math

import pandas as pd

LOOKBACK_DAYS = 90
VOL_WINDOW = 20
RANGE_WINDOW = 20
HOLD_DAYS = 8
MIN_HISTORY = 45
MIN_ABS_CLOSE_TO_CLOSE = 0.035
MIN_VOLUME_MULTIPLE = 1.55
MIN_RANGE_MULTIPLE = 1.20
MIN_CLOSE_LOCATION_EDGE = 0.68
MAX_ABS_SYMBOL_SCORE = 3.0
MAX_ABS_WEIGHT = 0.25


def _event_score(symbol_frame: pd.DataFrame) -> float:
    """Return the decayed continuation score from the latest proxy event."""
    df = symbol_frame.sort_values("timestamp").tail(LOOKBACK_DAYS).copy()
    if len(df) < MIN_HISTORY:
        return 0.0

    df["prev_close"] = df["close"].shift(1)
    df["close_to_close"] = df["close"] / df["prev_close"] - 1.0
    df["avg_volume"] = df["volume"].shift(1).rolling(VOL_WINDOW).mean()
    df["volume_multiple"] = df["volume"] / df["avg_volume"]
    df["intraday_range"] = (df["high"] - df["low"]) / df["prev_close"]
    df["avg_range"] = df["intraday_range"].shift(1).rolling(RANGE_WINDOW).mean()
    df["range_multiple"] = df["intraday_range"] / df["avg_range"]
    range_denom = (df["high"] - df["low"]).replace(0, pd.NA)
    df["close_location"] = ((df["close"] - df["low"]) / range_denom).astype(float)

    positive_event = (
        (df["close_to_close"] >= MIN_ABS_CLOSE_TO_CLOSE)
        & (df["close_location"] >= MIN_CLOSE_LOCATION_EDGE)
    )
    negative_event = (
        (df["close_to_close"] <= -MIN_ABS_CLOSE_TO_CLOSE)
        & (df["close_location"] <= (1.0 - MIN_CLOSE_LOCATION_EDGE))
    )
    events = df[
        (df["prev_close"] > 0)
        & (df["avg_volume"] > 0)
        & (df["avg_range"] > 0)
        & (df["volume_multiple"] >= MIN_VOLUME_MULTIPLE)
        & (df["range_multiple"] >= MIN_RANGE_MULTIPLE)
        & (positive_event | negative_event)
    ]
    if events.empty:
        return 0.0

    event = events.iloc[-1]
    event_position = df.index.get_loc(event.name)
    days_since = len(df) - 1 - event_position
    # Trade only after the event bar is complete; no same-day response.
    if days_since <= 0 or days_since > HOLD_DAYS:
        return 0.0

    direction = 1.0 if float(event["close_to_close"]) > 0 else -1.0
    shock_strength = min(abs(float(event["close_to_close"])) / MIN_ABS_CLOSE_TO_CLOSE, MAX_ABS_SYMBOL_SCORE)
    volume_strength = min(float(event["volume_multiple"]) / MIN_VOLUME_MULTIPLE, MAX_ABS_SYMBOL_SCORE)
    range_strength = min(float(event["range_multiple"]) / MIN_RANGE_MULTIPLE, MAX_ABS_SYMBOL_SCORE)
    decay = max(0.0, (HOLD_DAYS - days_since + 1) / HOLD_DAYS)
    score = direction * math.sqrt(shock_strength * volume_strength * range_strength) * decay
    return float(score) if math.isfinite(score) else 0.0


def generate_signals(context) -> dict[str, float]:
    """Generate normalized target weights keyed by symbol for qfa AlphaContext."""
    prices = context.prices.copy()
    if prices.empty:
        return {symbol: 0.0 for symbol in context.symbols}

    raw_scores = {}
    for symbol in context.symbols:
        frame = prices[prices["symbol"] == symbol]
        raw_scores[symbol] = _event_score(frame) if not frame.empty else 0.0

    gross = sum(abs(score) for score in raw_scores.values())
    if gross <= 0:
        return {symbol: 0.0 for symbol in context.symbols}

    weights = {symbol: score / gross for symbol, score in raw_scores.items()}
    clipped = {symbol: max(min(weight, MAX_ABS_WEIGHT), -MAX_ABS_WEIGHT) for symbol, weight in weights.items()}
    clipped_gross = sum(abs(weight) for weight in clipped.values())
    if clipped_gross <= 0:
        return {symbol: 0.0 for symbol in context.symbols}
    return {symbol: weight / clipped_gross for symbol, weight in clipped.items()}
