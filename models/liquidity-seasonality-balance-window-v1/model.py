"""AR-038 liquidity/seasonality balance-sheet-window alpha.

QFA contract: expose generate_signals(context) -> dict[str, float].
Research-only; uses only historical OHLCV bars supplied by qfa/Alpaca.

Mechanism tested here is deliberately different from event-drift: hold a
high-liquidity mega-cap basket only around calendar month/quarter balance-sheet
windows, when institutional cash, reporting, and balance-sheet constraints may
change demand for the most liquid equities. Outside those windows the model is
flat.
"""

from __future__ import annotations

import math

import pandas as pd
from pandas.tseries.offsets import BDay, BMonthEnd, QuarterEnd

UNIVERSE = (
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "META",
    "GOOGL",
    "AVGO",
    "JPM",
    "LLY",
    "XOM",
    "UNH",
    "COST",
)

PARAMS = {
    "pre_month_end_business_days": 2,
    "post_month_start_business_days": 2,
    "pre_quarter_end_business_days": 4,
    "post_quarter_start_business_days": 3,
    "liquidity_window": 20,
    "momentum_window": 60,
    "vol_window": 20,
    "min_history": 63,
    "top_n_month": 5,
    "top_n_quarter": 6,
    "max_abs_weight": 0.20,
    "min_symbols": 4,
    "gross_exposure": 1.0,
}


def _zero(symbols: list[str]) -> dict[str, float]:
    return {symbol: 0.0 for symbol in symbols}


def _as_utc_timestamp(value) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        return ts.tz_localize("UTC")
    return ts.tz_convert("UTC")


def _window_state(as_of: pd.Timestamp) -> str:
    """Return 'quarter', 'month', or '' for the no-lookahead seasonal window."""
    day = as_of.tz_convert("UTC").normalize().tz_localize(None)
    month_start = day.replace(day=1)
    month_end = month_start + BMonthEnd(0)
    month_pre_start = month_end - BDay(PARAMS["pre_month_end_business_days"] - 1)
    month_post_end = month_start + BDay(PARAMS["post_month_start_business_days"] - 1)
    in_month = bool(day >= month_pre_start or day <= month_post_end)

    quarter_end = day + QuarterEnd(0)
    quarter_start = pd.Timestamp(year=day.year, month=((day.month - 1) // 3) * 3 + 1, day=1)
    quarter_pre_start = quarter_end - BDay(PARAMS["pre_quarter_end_business_days"] - 1)
    quarter_post_end = quarter_start + BDay(PARAMS["post_quarter_start_business_days"] - 1)
    in_quarter = bool(day >= quarter_pre_start or day <= quarter_post_end)
    if in_quarter:
        return "quarter"
    if in_month:
        return "month"
    return ""


def _cap_normalize(raw_scores: dict[str, float], symbols: list[str]) -> dict[str, float]:
    scores = {s: max(0.0, float(raw_scores.get(s, 0.0))) for s in symbols}
    scores = {s: v for s, v in scores.items() if math.isfinite(v) and v > 0.0}
    if not scores:
        return _zero(symbols)

    cap = float(PARAMS["max_abs_weight"])
    target_gross = float(PARAMS["gross_exposure"])
    remaining = set(scores)
    assigned: dict[str, float] = {}
    gross_left = target_gross

    while remaining and gross_left > 1e-12:
        score_sum = sum(scores[s] for s in remaining)
        if score_sum <= 0.0:
            break
        tentative = {s: gross_left * scores[s] / score_sum for s in remaining}
        violators = {s for s, w in tentative.items() if w > cap}
        if not violators:
            assigned.update(tentative)
            break
        for s in violators:
            assigned[s] = cap
            remaining.remove(s)
            gross_left -= cap

    gross = sum(abs(v) for v in assigned.values())
    if gross <= 0.0:
        return _zero(symbols)
    scale = min(1.0, target_gross / gross)
    return {s: float(assigned.get(s, 0.0) * scale) for s in symbols}


def generate_signals(context):
    """Return target weights for liquid mega-caps around balance-sheet windows."""
    output_symbols = list(getattr(context, "symbols", []) or [])
    symbols = [s for s in output_symbols if s in UNIVERSE]
    if len(symbols) < PARAMS["min_symbols"]:
        return _zero(output_symbols)

    as_of = _as_utc_timestamp(getattr(context, "as_of", pd.Timestamp.utcnow()))
    state = _window_state(as_of)
    if not state:
        return _zero(output_symbols)

    prices = getattr(context, "prices", pd.DataFrame())
    if prices is None or prices.empty:
        return _zero(output_symbols)
    df = prices.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df[df["symbol"].isin(symbols)].sort_values(["timestamp", "symbol"])
    close = df.pivot(index="timestamp", columns="symbol", values="close").ffill()
    volume = df.pivot(index="timestamp", columns="symbol", values="volume").ffill()
    close = close.dropna(axis=1, how="any")
    tradable = [s for s in symbols if s in close.columns and s in volume.columns]
    if len(tradable) < PARAMS["min_symbols"] or len(close) < PARAMS["min_history"]:
        return _zero(output_symbols)

    close = close.loc[:as_of, tradable]
    volume = volume.loc[:as_of, tradable]
    if len(close) < PARAMS["min_history"]:
        return _zero(output_symbols)

    dollar_volume = (close * volume).tail(PARAMS["liquidity_window"]).mean()
    returns = close.pct_change()
    vol = returns.tail(PARAMS["vol_window"]).std(ddof=1).replace(0.0, pd.NA)
    momentum = close.iloc[-1] / close.iloc[-1 - PARAMS["momentum_window"]] - 1.0

    # Balance-sheet windows are expected to favor names that are easy to source
    # liquidity in; require non-negative medium-term trend to avoid catching
    # falling knives, then tilt to high dollar volume per unit volatility.
    score = (dollar_volume.rank(pct=True) * 0.70) + ((1.0 / vol).rank(pct=True) * 0.30)
    score = score[(momentum >= 0.0) & score.notna()]
    if len(score) < PARAMS["min_symbols"]:
        return _zero(output_symbols)

    top_n = PARAMS["top_n_quarter"] if state == "quarter" else PARAMS["top_n_month"]
    selected = score.sort_values(ascending=False).head(top_n)
    raw = {s: float(selected.get(s, 0.0)) for s in output_symbols}
    return _cap_normalize(raw, output_symbols)
