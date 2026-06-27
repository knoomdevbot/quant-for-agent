"""AR-030 earnings-quality/post-event drift proxy for mega-cap equities.

qfa/Alpaca in this repository supplies real OHLCV bars but not a dependable
fundamental earnings calendar. This research model therefore does **not**
fabricate earnings dates. It uses a documented price-only event proxy:
large overnight/close-to-close information shock with abnormal volume, followed
by positive/negative post-event drift and stable realized volatility.

Mechanism: firms that absorb an information shock and then continue drifting in
that direction while volatility remains stable may proxy for earnings-quality or
post-event underreaction. This is event-gated and drift-conditioned, not a pure
low-volatility ranker.
"""

from __future__ import annotations

import math

import pandas as pd

UNIVERSE = (
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "META",
    "GOOGL",
    "TSLA",
    "JNJ",
    "PG",
    "KO",
    "PEP",
    "WMT",
)

LOOKBACK_DAYS = 160
EVENT_SCAN_DAYS = 45
HOLD_DAYS = 20
VOL_WINDOW = 60
VOLUME_WINDOW = 20
MIN_HISTORY = 85
MIN_ABS_EVENT_RETURN = 0.025
MIN_VOLUME_MULTIPLE = 1.30
MIN_POST_EVENT_ABS_DRIFT = 0.008
MAX_ABS_WEIGHT = 0.22
MAX_ABS_SCORE = 4.0
MIN_ACTIVE_NAMES = 2


def _safe_float(value, default: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return default
    return out if math.isfinite(out) else default


def _symbol_score(frame: pd.DataFrame) -> float:
    """Score latest active event by direction, post-event drift, and vol stability."""
    df = frame.sort_values("timestamp").tail(LOOKBACK_DAYS).copy()
    if len(df) < MIN_HISTORY:
        return 0.0

    df["prev_close"] = df["close"].shift(1)
    df["cc_return"] = df["close"] / df["prev_close"] - 1.0
    df["overnight_gap"] = df["open"] / df["prev_close"] - 1.0
    df["avg_volume"] = df["volume"].shift(1).rolling(VOLUME_WINDOW).mean()
    df["volume_multiple"] = df["volume"] / df["avg_volume"]
    df["daily_ret"] = df["close"].pct_change()
    df["realized_vol"] = df["daily_ret"].rolling(VOL_WINDOW).std()
    df["pre_event_vol"] = df["daily_ret"].shift(1).rolling(VOL_WINDOW).std()

    # Large information-shock proxy: close-to-close or overnight move with abnormal volume.
    event_mask = (
        (df["prev_close"] > 0)
        & (df["avg_volume"] > 0)
        & (df["volume_multiple"] >= MIN_VOLUME_MULTIPLE)
        & (
            (df["cc_return"].abs() >= MIN_ABS_EVENT_RETURN)
            | (df["overnight_gap"].abs() >= MIN_ABS_EVENT_RETURN)
        )
    )
    events = df.tail(EVENT_SCAN_DAYS)[event_mask.tail(EVENT_SCAN_DAYS)]
    if events.empty:
        return 0.0

    # Use the most recent event that has at least two completed post-event bars.
    for event_index, event in reversed(list(events.iterrows())):
        event_pos = df.index.get_loc(event_index)
        days_since = len(df) - 1 - event_pos
        if days_since < 2 or days_since > HOLD_DAYS:
            continue

        event_close = _safe_float(event["close"])
        latest_close = _safe_float(df["close"].iloc[-1])
        if event_close <= 0 or latest_close <= 0:
            continue
        post_event_drift = latest_close / event_close - 1.0
        if abs(post_event_drift) < MIN_POST_EVENT_ABS_DRIFT:
            continue

        direction = 1.0 if _safe_float(event["cc_return"]) >= 0 else -1.0
        # Require the drift to confirm the event direction; otherwise no direct inversion.
        if direction * post_event_drift <= 0:
            continue

        pre_vol = _safe_float(event.get("pre_event_vol"))
        current_vol = _safe_float(df["realized_vol"].iloc[-1])
        if pre_vol <= 0 or current_vol <= 0:
            continue
        vol_ratio = current_vol / pre_vol
        # Stable-vol quality proxy: reward modest/stable vol, penalize post-event volatility expansion.
        stability = max(0.0, min(1.5, 1.25 - max(0.0, vol_ratio - 1.0)))
        if stability <= 0:
            continue

        event_strength = min(MAX_ABS_SCORE, abs(_safe_float(event["cc_return"])) / MIN_ABS_EVENT_RETURN)
        volume_strength = min(MAX_ABS_SCORE, _safe_float(event["volume_multiple"]) / MIN_VOLUME_MULTIPLE)
        drift_strength = min(MAX_ABS_SCORE, abs(post_event_drift) / MIN_POST_EVENT_ABS_DRIFT)
        decay = max(0.0, (HOLD_DAYS - days_since + 1) / HOLD_DAYS)
        score = direction * math.sqrt(event_strength * volume_strength * drift_strength) * stability * decay
        return score if math.isfinite(score) else 0.0

    return 0.0


def generate_signals(context) -> dict[str, float]:
    """Return qfa target weights for the next daily bar."""
    output_symbols = list(context.symbols)
    if context.prices is None or context.prices.empty:
        return {symbol: 0.0 for symbol in output_symbols}

    prices = context.prices.copy()
    prices["timestamp"] = pd.to_datetime(prices["timestamp"], utc=True)

    raw_scores = {}
    for symbol in output_symbols:
        if symbol not in UNIVERSE:
            raw_scores[symbol] = 0.0
            continue
        frame = prices[prices["symbol"] == symbol]
        raw_scores[symbol] = _symbol_score(frame) if not frame.empty else 0.0

    active = {s: v for s, v in raw_scores.items() if math.isfinite(v) and abs(v) > 0.0}
    if len(active) < MIN_ACTIVE_NAMES:
        return {symbol: 0.0 for symbol in output_symbols}

    gross = sum(abs(v) for v in active.values())
    weights = {s: active.get(s, 0.0) / gross for s in output_symbols}
    clipped = {s: max(min(w, MAX_ABS_WEIGHT), -MAX_ABS_WEIGHT) for s, w in weights.items()}
    clipped_gross = sum(abs(w) for w in clipped.values())
    if clipped_gross <= 0:
        return {symbol: 0.0 for symbol in output_symbols}
    return {s: clipped[s] / clipped_gross for s in output_symbols}
