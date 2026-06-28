"""
CFTC COT positioning extreme-unwind ETF allocator (AR-135).

QFA contract: expose generate_signals(context) -> dict[str, float].  The model is
research-only and expects timestamp-safe weekly COT features to be supplied on the
context as ``cot_features``/``extra['cot_features']`` or as a dataframe-like
``cot_signal_history`` with columns symbol, cot_z, cot_delta4_z, release_date.
It never fetches data, starts daemons, or places orders.

Signal rule fixed for evaluation:
- use only features whose public release date is <= context.as_of;
- contrarian unwind direction is opposite the extreme speculative/fund net
  positioning z-score;
- activate only when |cot_z| >= 1.5 and either the 4-week net-position change is
  already reversing the crowded direction or recent ETF momentum is not strongly
  confirming it;
- cap each symbol at 20% and gross exposure at 100%.
"""

from __future__ import annotations

from typing import Any

CANDIDATE_SYMBOLS = [
    "GLD", "SLV", "USO", "UNG", "DBA", "DBC", "PDBC", "GSG",
    "TLT", "IEF", "SHY", "TIP", "UUP", "FXE", "FXY", "SPY", "QQQ", "IWM", "DIA",
]
SELECTED_SYMBOLS = ["GLD", "SLV", "USO", "UNG", "TLT", "IEF", "UUP", "SPY", "QQQ", "IWM"]
EXTREME_Z = 1.5
MAX_WEIGHT = 0.20
GROSS_CAP = 1.00
MOM_LOOKBACK = 20
MOM_CONFIRM_THRESHOLD = 0.015


def _prices(context: Any):
    return getattr(context, "prices", None)


def _as_of(context: Any):
    return getattr(context, "as_of", None)


def _latest_cot_features(context: Any) -> dict[str, dict[str, float]]:
    direct = getattr(context, "cot_features", None)
    if direct is None and isinstance(getattr(context, "extra", None), dict):
        direct = context.extra.get("cot_features")
    if isinstance(direct, dict):
        return direct

    hist = getattr(context, "cot_signal_history", None)
    if hist is None and isinstance(getattr(context, "extra", None), dict):
        hist = context.extra.get("cot_signal_history")
    if hist is None:
        return {}

    try:
        import pandas as pd

        df = hist.copy()
        as_of_value = _as_of(context)
        if as_of_value is None:
            return {}
        as_of = pd.Timestamp(as_of_value)
        if as_of.tzinfo is not None:
            as_of = as_of.tz_convert(None)
        date_col = "release_date" if "release_date" in df.columns else "date"
        df[date_col] = pd.to_datetime(df[date_col]).dt.tz_localize(None)
        df = df[df[date_col] <= as_of].sort_values(date_col)
        latest = df.groupby("symbol").tail(1)
        return {
            str(r["symbol"]): {
                "cot_z": float(r.get("cot_z", 0.0)),
                "cot_delta4_z": float(r.get("cot_delta4_z", 0.0)),
            }
            for _, r in latest.iterrows()
        }
    except Exception:
        return {}


def _momentum_by_symbol(context: Any, symbols: list[str]) -> dict[str, float]:
    prices = _prices(context)
    if prices is None:
        return {s: 0.0 for s in symbols}
    try:
        import pandas as pd

        df = prices.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        close = df[df["symbol"].isin(symbols)].pivot(index="timestamp", columns="symbol", values="close").sort_index().ffill()
        if len(close) <= MOM_LOOKBACK:
            return {s: 0.0 for s in symbols}
        mom = close.iloc[-1] / close.iloc[-1 - MOM_LOOKBACK] - 1.0
        return {s: float(mom.get(s, 0.0)) for s in symbols}
    except Exception:
        return {s: 0.0 for s in symbols}


def generate_signals(context: Any) -> dict[str, float]:
    symbols = list(getattr(context, "symbols", SELECTED_SYMBOLS) or SELECTED_SYMBOLS)
    symbols = [s for s in symbols if s in SELECTED_SYMBOLS]
    features = _latest_cot_features(context)
    if not features:
        return {s: 0.0 for s in symbols}
    mom = _momentum_by_symbol(context, symbols)
    raw: dict[str, float] = {}
    for symbol in symbols:
        f = features.get(symbol, {})
        z = float(f.get("cot_z", 0.0) or 0.0)
        d4 = float(f.get("cot_delta4_z", 0.0) or 0.0)
        if abs(z) < EXTREME_Z:
            continue
        crowded_dir = 1.0 if z > 0 else -1.0
        reversing = d4 * crowded_dir < 0.0
        stalled = mom.get(symbol, 0.0) * crowded_dir < MOM_CONFIRM_THRESHOLD
        if reversing or stalled:
            raw[symbol] = max(-MAX_WEIGHT, min(MAX_WEIGHT, -crowded_dir * min(MAX_WEIGHT, 0.08 + 0.04 * min(abs(z), 3.0))))
    gross = sum(abs(v) for v in raw.values())
    if gross > GROSS_CAP and gross > 0:
        raw = {k: v * GROSS_CAP / gross for k, v in raw.items()}
    return {s: float(raw.get(s, 0.0)) for s in symbols}
