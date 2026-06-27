"""AR-042 scheduled macro/liquidity ETF flow pressure alpha.

Research-only qfa model using only OHLCV history supplied by qfa/Alpaca plus
calendar features that are deterministic from the as-of date.  The hypothesis is
that recurring macro/liquidity-risk periods (payroll/CPI/FOMC-like windows) can
interact with cross-asset ETF breadth and flow-pressure proxies differently from
plain month-end seasonality.
"""

from __future__ import annotations

import math

import pandas as pd
from pandas.tseries.offsets import BDay

UNIVERSE = ("SPY", "QQQ", "IWM", "TLT", "GLD", "XLU", "XLE")
CORE = ("SPY", "QQQ", "IWM", "TLT", "GLD")
DEFENSIVE = ("TLT", "GLD", "XLU")
RISK = ("SPY", "QQQ", "IWM", "XLE")

PARAMS = {
    "min_history": 126,
    "short_window": 5,
    "medium_window": 21,
    "slow_window": 63,
    "vol_window": 21,
    "volume_window": 21,
    "gross_event": 1.0,
    "gross_non_event": 0.35,
    "max_weight": 0.35,
}


def _zero(symbols: list[str]) -> dict[str, float]:
    return {s: 0.0 for s in symbols}


def _safe(value, default: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return default
    return out if math.isfinite(out) else default


def _as_utc(value) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    return ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")


def _first_friday(day: pd.Timestamp) -> pd.Timestamp:
    month_start = pd.Timestamp(day.year, day.month, 1)
    return month_start + pd.offsets.Week(weekday=4)


def _nth_weekday(day: pd.Timestamp, weekday: int, n: int) -> pd.Timestamp:
    month_start = pd.Timestamp(day.year, day.month, 1)
    first = month_start + pd.offsets.Week(weekday=weekday)
    if first.month != day.month:
        first = first + pd.offsets.Week(weekday=weekday)
    return first + pd.offsets.Week(n=n - 1)


def _event_state(as_of: pd.Timestamp) -> tuple[bool, str]:
    """Deterministic macro/liquidity proxies, intentionally not month-end based."""
    day = as_of.tz_convert("UTC").normalize().tz_localize(None)
    # Payroll proxy: first-Friday window, one business day before through one after.
    payroll = _first_friday(day)
    if payroll - BDay(1) <= day <= payroll + BDay(1):
        return True, "payroll_proxy"
    # CPI proxy: common release cluster around the 10th-14th; use mid-month Tue/Wed/Thu.
    if 10 <= day.day <= 14 and day.weekday() in (1, 2, 3):
        return True, "cpi_proxy"
    # FOMC proxy: third Wednesday in regular meeting months, +/- one business day.
    if day.month in (1, 3, 5, 6, 7, 9, 11, 12):
        fomc = _nth_weekday(day, weekday=2, n=3)
        if fomc - BDay(1) <= day <= fomc + BDay(1):
            return True, "fomc_proxy"
    # Mid-quarter liquidity checkpoint, separate from month boundaries.
    if day.month in (2, 5, 8, 11) and 14 <= day.day <= 18 and day.weekday() <= 3:
        return True, "midquarter_liquidity_proxy"
    return False, "none"


def _ret(close: pd.DataFrame, symbol: str, window: int) -> float:
    if symbol not in close.columns or len(close[symbol].dropna()) <= window:
        return 0.0
    s = close[symbol].dropna()
    if s.iloc[-window - 1] <= 0:
        return 0.0
    return _safe(s.iloc[-1] / s.iloc[-window - 1] - 1.0)


def _vol(close: pd.DataFrame, symbol: str, window: int) -> float:
    if symbol not in close.columns:
        return 0.0
    r = close[symbol].dropna().pct_change().dropna().tail(window)
    return _safe(r.std(ddof=1) * math.sqrt(252.0)) if len(r) > 2 else 0.0


def _volume_pressure(close: pd.DataFrame, volume: pd.DataFrame, symbol: str) -> float:
    if symbol not in close.columns or symbol not in volume.columns:
        return 0.0
    dollar_vol = (close[symbol] * volume[symbol]).dropna()
    w = PARAMS["volume_window"]
    if len(dollar_vol) < 2 * w:
        return 0.0
    recent = dollar_vol.tail(5).mean()
    base = dollar_vol.tail(w).mean()
    return _safe(recent / base - 1.0) if base > 0 else 0.0


def _normalize(scores: dict[str, float], symbols: list[str], gross: float) -> dict[str, float]:
    positives = {s: max(0.0, _safe(scores.get(s, 0.0))) for s in symbols}
    total = sum(positives.values())
    if gross <= 0 or total <= 0:
        return _zero(symbols)
    weights = {s: gross * positives[s] / total for s in symbols}
    cap = PARAMS["max_weight"]
    capped = {s: min(cap, w) for s, w in weights.items()}
    capped_total = sum(capped.values())
    if capped_total > gross and capped_total > 0:
        capped = {s: w * gross / capped_total for s, w in capped.items()}
    return {s: _safe(capped.get(s, 0.0)) for s in symbols}


def generate_signals(context) -> dict[str, float]:
    symbols = list(getattr(context, "symbols", []) or [])
    tradable = [s for s in symbols if s in UNIVERSE]
    if len([s for s in tradable if s in CORE]) < 5:
        return _zero(symbols)

    prices = getattr(context, "prices", pd.DataFrame())
    if prices is None or prices.empty:
        return _zero(symbols)
    df = prices.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    as_of = _as_utc(getattr(context, "as_of", df["timestamp"].max()))
    df = df[(df["symbol"].isin(tradable)) & (df["timestamp"] <= as_of)].sort_values(["timestamp", "symbol"])
    close = df.pivot(index="timestamp", columns="symbol", values="close").ffill()
    volume = df.pivot(index="timestamp", columns="symbol", values="volume").ffill()
    if len(close) < PARAMS["min_history"]:
        return _zero(symbols)

    is_event, _label = _event_state(as_of)
    breadth = sum(1 for s in CORE if _ret(close, s, PARAMS["medium_window"]) > 0) / len(CORE)
    equity_breadth = sum(1 for s in ("SPY", "QQQ", "IWM") if _ret(close, s, PARAMS["short_window"]) > 0) / 3.0
    duration_gold = 0.5 * _ret(close, "TLT", PARAMS["medium_window"]) + 0.5 * _ret(close, "GLD", PARAMS["medium_window"])
    equity_mom = (0.45 * _ret(close, "SPY", PARAMS["medium_window"]) + 0.35 * _ret(close, "QQQ", PARAMS["medium_window"]) + 0.20 * _ret(close, "IWM", PARAMS["medium_window"]))
    risk_pressure = equity_mom - duration_gold
    spy_vol = _vol(close, "SPY", PARAMS["vol_window"])
    stress = max(0.0, min(1.0, 0.50 - 1.8 * risk_pressure + max(0.0, spy_vol - 0.18) * 1.2 + (0.5 - equity_breadth) * 0.6))

    gross = PARAMS["gross_event"] if is_event else PARAMS["gross_non_event"]
    # Event days: lean into whichever side has recent pressure, but de-risk if breadth is weak.
    risk_budget = gross * (0.70 - 0.45 * stress + 0.20 * max(0.0, breadth - 0.5))
    risk_budget = max(0.0, min(gross, risk_budget))
    defensive_budget = gross - risk_budget

    risk_scores = {}
    for s in ("SPY", "QQQ", "IWM", "XLE"):
        if s in tradable:
            risk_scores[s] = 1.0 + 3.0 * max(0.0, _ret(close, s, PARAMS["short_window"])) + max(0.0, _volume_pressure(close, volume, s))
    defensive_scores = {}
    for s in ("TLT", "GLD", "XLU"):
        if s in tradable:
            defensive_scores[s] = 1.0 + 3.0 * max(0.0, _ret(close, s, PARAMS["short_window"])) + max(0.0, _volume_pressure(close, volume, s))

    weights = _zero(symbols)
    risk_w = _normalize(risk_scores, symbols, risk_budget)
    def_w = _normalize(defensive_scores, symbols, defensive_budget)
    for s in symbols:
        weights[s] = _safe(risk_w.get(s, 0.0) + def_w.get(s, 0.0))
    return weights
