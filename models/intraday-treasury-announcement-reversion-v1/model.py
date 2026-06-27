"""AR-078 intraday Treasury ETF post-announcement reversal model.

Research-only qfa-compatible alpha.  The strategy is deliberately inert unless
an evaluator supplies explicit, already-public event metadata in
``context.metadata``.  This prevents accidental daily AR-070 substitution and
avoids timestamp leakage in ordinary qfa backtests, whose CLI currently has no
native event-calendar argument.

Expected metadata keys:
    event_ts_utc: ISO timestamp of public macro announcement (UTC)
    shock_minutes: minutes after announcement used to measure overreaction
    hold_minutes: intended hold horizon after signal timestamp
    event_type: e.g. FOMC or CPI (audit only)

Signal: at event_ts + shock_minutes, fade the observed duration ETF shock using
only bars timestamped <= context.as_of.  Gross exposure is capped at 1.0.
"""
from __future__ import annotations

import math
from typing import Dict

import pandas as pd

UNIVERSE = ("SHY", "IEF", "TLT", "TIP", "LQD", "HYG", "GLD", "SPY")
DURATION_SYMBOLS = ("IEF", "TLT")
MAX_GROSS = 1.0
MAX_SINGLE = 0.45
MIN_ABS_SHOCK = 0.00045  # 4.5 bps over the event shock window
DEFAULT_SHOCK_MINUTES = 60
DEFAULT_HOLD_MINUTES = 60


def _flat(symbols) -> Dict[str, float]:
    return {s: 0.0 for s in symbols}


def _safe_float(value, default: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return default
    return out if math.isfinite(out) else default


def _as_utc(ts) -> pd.Timestamp | None:
    if ts is None:
        return None
    try:
        out = pd.Timestamp(ts)
    except Exception:
        return None
    if out.tzinfo is None:
        out = out.tz_localize("UTC")
    else:
        out = out.tz_convert("UTC")
    return out


def _normalize(weights: Dict[str, float]) -> Dict[str, float]:
    capped = {s: max(-MAX_SINGLE, min(MAX_SINGLE, _safe_float(v))) for s, v in weights.items()}
    gross = sum(abs(v) for v in capped.values())
    if gross <= 0:
        return capped
    if gross > MAX_GROSS:
        capped = {s: v / gross * MAX_GROSS for s, v in capped.items()}
    return capped


def generate_signals(context) -> dict[str, float]:
    symbols = list(getattr(context, "symbols", []) or [])
    weights = _flat(symbols)
    metadata = dict(getattr(context, "metadata", {}) or {})

    event_ts = _as_utc(metadata.get("event_ts_utc"))
    as_of = _as_utc(getattr(context, "as_of", None))
    if event_ts is None or as_of is None:
        return weights

    shock_minutes = int(metadata.get("shock_minutes", DEFAULT_SHOCK_MINUTES))
    signal_ts = event_ts + pd.Timedelta(minutes=shock_minutes)
    # Only allow the signal at/after the shock measurement point and before the
    # intended hold horizon expires.  Evaluators should set context.as_of exactly
    # to signal_ts; this guard keeps accidental calls safe.
    hold_minutes = int(metadata.get("hold_minutes", DEFAULT_HOLD_MINUTES))
    if as_of < signal_ts or as_of > signal_ts + pd.Timedelta(minutes=max(hold_minutes, 1)):
        return weights

    prices = getattr(context, "prices", None)
    if prices is None or prices.empty:
        return weights
    df = prices.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    close = df.pivot(index="timestamp", columns="symbol", values="close").sort_index().ffill()
    available = [s for s in UNIVERSE if s in symbols and s in close.columns]
    if not set(DURATION_SYMBOLS).issubset(available):
        return weights

    hist = close.loc[close.index <= as_of]
    pre = hist.loc[hist.index <= event_ts]
    post = hist.loc[hist.index <= signal_ts]
    if pre.empty or post.empty:
        return weights
    pre_px = pre.iloc[-1]
    sig_px = post.iloc[-1]
    ret_ief = _safe_float(sig_px.get("IEF") / pre_px.get("IEF") - 1.0)
    ret_tlt = _safe_float(sig_px.get("TLT") / pre_px.get("TLT") - 1.0)
    duration_shock = 0.40 * ret_ief + 0.60 * ret_tlt
    if abs(duration_shock) < MIN_ABS_SHOCK:
        return weights

    raw = {s: 0.0 for s in symbols}
    shock_scale = min(1.0, abs(duration_shock) / 0.0030)
    budget = 0.35 + 0.65 * shock_scale
    if duration_shock < 0.0:
        # Treasury selloff overreaction: buy duration reversal.
        raw["TLT"] = 0.45 * budget if "TLT" in symbols else 0.0
        raw["IEF"] = 0.35 * budget if "IEF" in symbols else 0.0
        raw["TIP"] = 0.12 * budget if "TIP" in symbols else 0.0
        raw["GLD"] = 0.08 * budget if "GLD" in symbols else 0.0
    else:
        # Treasury rally overreaction: fade by reducing duration via SHY/TIP and
        # limited risk/credit sleeves rather than relying on hard-to-borrow shorts.
        raw["SHY"] = 0.42 * budget if "SHY" in symbols else 0.0
        raw["TIP"] = 0.22 * budget if "TIP" in symbols else 0.0
        raw["LQD"] = 0.14 * budget if "LQD" in symbols else 0.0
        raw["SPY"] = 0.10 * budget if "SPY" in symbols else 0.0
    return _normalize(raw)
