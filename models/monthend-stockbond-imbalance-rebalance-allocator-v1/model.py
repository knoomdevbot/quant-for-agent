"""AR-125 month-end stock/bond imbalance rebalancing allocator.

QFA contract: expose generate_signals(context) -> dict[str, float].
Research-only model; no orders. Uses timestamp-safe daily OHLCV history supplied by qfa/Alpaca.
"""
from __future__ import annotations

import math
import pandas as pd

EQUITY = ("SPY", "QQQ", "IWM", "DIA", "XLK", "XLF", "XLE", "XLY", "XLP", "XLI", "XLU", "XLV", "XLB", "XLRE")
BONDS = ("TLT", "IEF", "SHY", "LQD", "HYG", "AGG", "BND", "TIP")
UNIVERSE = EQUITY + BONDS + ("GLD", "UUP")
MIN_HISTORY = 80
IMBALANCE_THRESHOLD = 0.01
GROSS_EXPOSURE = 1.0
EQUITY_BUDGET = 0.50
BOND_BUDGET = 0.50


def _safe(x: float) -> float:
    try:
        x = float(x)
    except Exception:
        return 0.0
    return x if math.isfinite(x) else 0.0


def _basket_return(close: pd.DataFrame, symbols: tuple[str, ...], start, end) -> float:
    vals = []
    for s in symbols:
        if s not in close.columns:
            continue
        ser = close[s].dropna()
        ser = ser[(ser.index >= start) & (ser.index <= end)]
        if len(ser) >= 2 and ser.iloc[0] > 0:
            vals.append(_safe(ser.iloc[-1] / ser.iloc[0] - 1.0))
    return _safe(sum(vals) / len(vals)) if vals else 0.0


def _prior_completed_month_imbalance(close: pd.DataFrame, as_of: pd.Timestamp) -> float:
    month_start = pd.Timestamp(year=as_of.year, month=as_of.month, day=1, tz=as_of.tz)
    prior = close[close.index < month_start]
    if prior.empty:
        return 0.0
    last_prior = prior.index[-1]
    prior_start = pd.Timestamp(year=last_prior.year, month=last_prior.month, day=1, tz=last_prior.tz)
    eq = _basket_return(close, EQUITY, prior_start, last_prior)
    bd = _basket_return(close, BONDS, prior_start, last_prior)
    return _safe(eq - bd)


def _is_calendar_turn_window(as_of: pd.Timestamp) -> bool:
    # qfa weights decided at as_of and applied to the next bar. This calendar proxy
    # targets the predeclared last-2/first-2 trading-day turn window without look-ahead.
    d = as_of.tz_convert(None) if getattr(as_of, 'tzinfo', None) is not None else as_of
    dim = d.days_in_month
    return (d.day >= dim - 3) or (d.day <= 2)


def _alloc(names: list[str], budget: float, sign: float) -> dict[str, float]:
    if not names or budget <= 0:
        return {}
    w = sign * budget / len(names)
    return {s: w for s in names}


def generate_signals(context) -> dict[str, float]:
    symbols = list(context.symbols)
    weights = {s: 0.0 for s in symbols}
    if context.prices is None or context.prices.empty:
        return weights
    px = context.prices.copy()
    px["timestamp"] = pd.to_datetime(px["timestamp"], utc=True)
    close = px.pivot(index="timestamp", columns="symbol", values="close").sort_index().ffill()
    as_of = pd.Timestamp(context.as_of)
    if as_of.tzinfo is None:
        as_of = as_of.tz_localize("UTC")
    close = close[close.index <= as_of]
    if len(close) < MIN_HISTORY or not _is_calendar_turn_window(as_of):
        return weights
    available_eq = [s for s in symbols if s in EQUITY and s in close.columns]
    available_bd = [s for s in symbols if s in BONDS and s in close.columns]
    if len(available_eq) < 4 or len(available_bd) < 4:
        return weights
    imbalance = _prior_completed_month_imbalance(close, as_of)
    if abs(imbalance) < IMBALANCE_THRESHOLD:
        return weights
    # Rebalance-pressure reversal: equity outperformance => buy bonds/sell equities; bond outperformance => buy equities/sell bonds.
    direction = -1.0 if imbalance > 0 else 1.0
    weights.update(_alloc(available_eq, EQUITY_BUDGET * GROSS_EXPOSURE, direction))
    weights.update(_alloc(available_bd, BOND_BUDGET * GROSS_EXPOSURE, -direction))
    return weights
