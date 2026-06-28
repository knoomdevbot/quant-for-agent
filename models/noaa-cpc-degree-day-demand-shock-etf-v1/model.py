"""
NOAA/CPC degree-day demand-shock ETF allocator (AR-136).

QFA contract: expose generate_signals(context) -> dict[str, float]. The model is
research-only and expects timestamp-safe NOAA/CPC weekly degree-day features to be
supplied on context as ``degree_day_features`` / ``extra['degree_day_features']``
or as a dataframe-like ``degree_day_signal_history`` with release_date,
cdd_week_dev_from_norm, and hdd_week_dev_from_norm columns. It never fetches data,
starts daemons, or places orders.

Evaluated rule: use only CPC records whose archive modified/release timestamp is
<= context.as_of; because the archive timezone is not stated, the evaluator traded
no earlier than the next regular session after the visible modified calendar date.
"""

from __future__ import annotations

from typing import Any

SELECTED_SYMBOLS = ["UNG", "USO", "XLE", "XOP", "XLU", "ICLN", "TAN"]
ACTIVE_THRESHOLD = 0.75
GROSS_CAP = 1.0


def _as_of(context: Any):
    return getattr(context, "as_of", None)


def _latest_features(context: Any) -> dict[str, Any]:
    direct = getattr(context, "degree_day_features", None)
    if direct is None and isinstance(getattr(context, "extra", None), dict):
        direct = context.extra.get("degree_day_features")
    if isinstance(direct, dict):
        return direct

    hist = getattr(context, "degree_day_signal_history", None)
    if hist is None and isinstance(getattr(context, "extra", None), dict):
        hist = context.extra.get("degree_day_signal_history")
    if hist is None or _as_of(context) is None:
        return {}
    try:
        import pandas as pd

        df = hist.copy()
        date_col = "release_date" if "release_date" in df.columns else "signal_trade_date"
        as_of_value = _as_of(context)
        if as_of_value is None:
            return {}
        as_of = pd.Timestamp(as_of_value)
        if as_of.tzinfo is not None:
            as_of = as_of.tz_convert(None)
        df[date_col] = pd.to_datetime(df[date_col]).dt.tz_localize(None)
        df = df[df[date_col] <= as_of].sort_values(date_col)
        if df.empty:
            return {}
        row = df.iloc[-1]
        return {
            "period_end": str(row.get("period_end", "")),
            "cdd_week_dev_from_norm": float(row.get("cdd_week_dev_from_norm", 0.0) or 0.0),
            "hdd_week_dev_from_norm": float(row.get("hdd_week_dev_from_norm", 0.0) or 0.0),
            "demand_shock": float(row.get("demand_shock", 0.0) or 0.0),
        }
    except Exception:
        return {}


def _demand_shock(features: dict[str, Any]) -> float:
    if "demand_shock" in features:
        return float(features.get("demand_shock", 0.0) or 0.0)
    cdd = float(features.get("cdd_week_dev_from_norm", 0.0) or 0.0)
    hdd = float(features.get("hdd_week_dev_from_norm", 0.0) or 0.0)
    period = str(features.get("period_end", ""))
    try:
        month = int(period[5:7])
    except Exception:
        month = 0
    warm_cdd = 1.0 if month in {4, 5, 6, 7, 8, 9, 10} else 0.4
    cool_hdd = 1.0 if month in {1, 2, 3, 10, 11, 12} else 0.4
    return warm_cdd * cdd / 18.0 + cool_hdd * hdd / 28.0


def _weights_for_shock(shock: float) -> dict[str, float]:
    if abs(shock) < ACTIVE_THRESHOLD:
        return {s: 0.0 for s in SELECTED_SYMBOLS}
    sign = 1.0 if shock > 0 else -1.0
    mag = min(1.0, abs(shock) / 2.0)
    raw = {
        "UNG": 0.25 * sign,
        "USO": 0.10 * sign,
        "XLE": 0.17 * sign,
        "XOP": 0.18 * sign,
        "XLU": -0.15 * sign,
        "ICLN": -0.08 * sign,
        "TAN": -0.07 * sign,
    }
    weights = {k: v * mag for k, v in raw.items()}
    gross = sum(abs(v) for v in weights.values())
    if gross > GROSS_CAP and gross > 0:
        weights = {k: v / gross * GROSS_CAP for k, v in weights.items()}
    return weights


def generate_signals(context: Any) -> dict[str, float]:
    symbols = list(getattr(context, "symbols", SELECTED_SYMBOLS) or SELECTED_SYMBOLS)
    symbols = [s for s in symbols if s in SELECTED_SYMBOLS]
    features = _latest_features(context)
    weights = _weights_for_shock(_demand_shock(features)) if features else {s: 0.0 for s in SELECTED_SYMBOLS}
    return {symbol: float(weights.get(symbol, 0.0)) for symbol in symbols}
