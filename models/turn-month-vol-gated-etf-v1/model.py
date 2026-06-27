"""AR-041 volatility-gated turn-of-month ETF seasonality alpha.

QFA contract: expose generate_signals(context) -> dict[str, float].
The model uses only qfa-provided OHLCV context and context.as_of.

Signal definition:
- active only during the AR-021 observed-data turn-of-month window: final 1
  observed session of the calendar month plus first 4 observed sessions;
- long equal-weight SPY/QQQ/IWM/TLT/GLD when the volatility/risk gate is open;
- flat when SPY realized volatility is elevated, short-term volatility is high
  versus its 60-session baseline, or SPY trend/drawdown state is risk-off.

Note: the repository qfa backtester normalizes nonzero gross weights to 1.0, so
volatility gating is implemented as active-vs-flat rather than fractional cash.
"""

from __future__ import annotations

import pandas as pd

DEFAULT_PARAMS = {
    "pre_month_end_observed_sessions": 1,
    "post_month_start_observed_sessions": 4,
    "realized_vol_window": 20,
    "baseline_vol_window": 60,
    "trend_window": 100,
    "drawdown_window": 60,
    "max_realized_vol": 0.25,
    "max_vol_ratio": 1.25,
    "max_drawdown_from_rolling_high": -0.08,
    "min_observations": 120,
    "max_abs_weight": 0.25,
}


def _params(context) -> dict:
    metadata = getattr(context, "metadata", {}) or {}
    provided = metadata.get("params", {}) if isinstance(metadata, dict) else {}
    params = DEFAULT_PARAMS.copy()
    params.update({k: provided[k] for k in params.keys() & provided.keys()})
    return params


def _as_timestamp(context) -> pd.Timestamp | None:
    as_of = getattr(context, "as_of", None)
    if as_of is not None:
        ts = pd.Timestamp(as_of)
        return ts.tz_convert("UTC") if ts.tzinfo else pd.Timestamp(ts, tz="UTC")
    prices = getattr(context, "prices", pd.DataFrame())
    if prices.empty or "timestamp" not in prices:
        return None
    return pd.to_datetime(prices["timestamp"], utc=True).max()


def _close_matrix(context, symbols: list[str]) -> pd.DataFrame:
    prices = getattr(context, "prices", pd.DataFrame())
    if prices.empty or not {"timestamp", "symbol", "close"}.issubset(prices.columns):
        return pd.DataFrame()
    frame = prices.loc[prices["symbol"].isin(symbols), ["timestamp", "symbol", "close"]].copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    return frame.pivot(index="timestamp", columns="symbol", values="close").sort_index().ffill()


def _is_observed_turn_of_month(close: pd.DataFrame, as_of: pd.Timestamp, pre_days: int, post_days: int) -> bool:
    """AR-021-compatible observed-session month-boundary proxy.

    This intentionally uses only sessions already present in qfa context, matching
    the parent AR-021 implementation and avoiding synthetic exchange calendars.
    """
    if close.empty:
        return False
    dates = close.index[close.index <= as_of]
    if len(dates) == 0:
        return False
    day = dates[-1].tz_convert("UTC").normalize()
    sessions = [stamp.tz_convert("UTC").normalize() for stamp in dates]
    month_sessions = [session for session in sessions if session.year == day.year and session.month == day.month]
    first_sessions = set(month_sessions[: max(int(post_days), 0)])
    last_sessions = set(month_sessions[-max(int(pre_days), 0) :]) if int(pre_days) > 0 else set()
    return bool(day in first_sessions or day in last_sessions)


def _risk_gate_open(close: pd.DataFrame, params: dict) -> bool:
    if "SPY" not in close or close["SPY"].dropna().shape[0] < int(params["min_observations"]):
        return False
    spy = close["SPY"].dropna()
    returns = spy.pct_change().dropna()
    vol_w = int(params["realized_vol_window"])
    base_w = int(params["baseline_vol_window"])
    trend_w = int(params["trend_window"])
    dd_w = int(params["drawdown_window"])
    if len(returns) < max(vol_w, base_w) or len(spy) < max(trend_w, dd_w):
        return False

    vol20 = float(returns.tail(vol_w).std() * (252 ** 0.5))
    vol60 = float(returns.tail(base_w).std() * (252 ** 0.5))
    latest = float(spy.iloc[-1])
    trend_ma = float(spy.tail(trend_w).mean())
    rolling_high = float(spy.tail(dd_w).max())
    drawdown = latest / rolling_high - 1.0 if rolling_high > 0 else -1.0

    absolute_vol_ok = vol20 <= float(params["max_realized_vol"])
    relative_vol_ok = (vol60 > 0) and (vol20 <= float(params["max_vol_ratio"]) * vol60)
    trend_ok = latest >= trend_ma
    drawdown_ok = drawdown >= float(params["max_drawdown_from_rolling_high"])
    return bool(absolute_vol_ok and relative_vol_ok and trend_ok and drawdown_ok)


def generate_signals(context):
    """Return volatility-gated turn-of-month target weights for context.symbols."""
    symbols = list(getattr(context, "symbols", []) or [])
    if not symbols:
        return {}
    params = _params(context)
    as_of = _as_timestamp(context)
    if as_of is None:
        return {symbol: 0.0 for symbol in symbols}

    close = _close_matrix(context, symbols)
    if not _is_observed_turn_of_month(
        close,
        as_of,
        int(params["pre_month_end_observed_sessions"]),
        int(params["post_month_start_observed_sessions"]),
    ):
        return {symbol: 0.0 for symbol in symbols}
    if not _risk_gate_open(close, params):
        return {symbol: 0.0 for symbol in symbols}

    active = [symbol for symbol in symbols if symbol in close.columns and close[symbol].dropna().shape[0] >= 2]
    if not active:
        return {symbol: 0.0 for symbol in symbols}
    weight = min(1.0 / len(active), float(params["max_abs_weight"]))
    return {symbol: (weight if symbol in active else 0.0) for symbol in symbols}
