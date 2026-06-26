"""AR-108 Treasury auction-week duration concession reversal ETF allocator.

QFA-compatible research model exposing generate_signals(context) -> dict[str, float].
The model uses only completed daily OHLCV bars supplied by qfa/Alpaca.  It gates
trades to deterministic Treasury coupon supply approximations known ex ante:
monthly nominal coupon auction/reopening weeks and quarterly refunding months.
After long duration underperforms short duration into the window and the latest
bar shows stabilization on lagged close-location/volume/return confirmation, it
allocates to a duration-reversal basket for a short horizon.  It is research-only
and never submits orders.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd

CANDIDATE_UNIVERSE = ("TLT", "IEF", "SHY", "TIP", "LQD", "HYG", "SPY", "GLD", "UUP")
SELECTED_UNIVERSE = CANDIDATE_UNIVERSE
DURATION_LEGS = ("TLT", "IEF", "TIP")
DEFENSIVE_LEG = "SHY"


@dataclass(frozen=True)
class Params:
    lookback: int = 5
    min_duration_concession: float = -0.006
    min_tlt_concession: float = -0.008
    stabilization_clv_min: float = 0.42
    stabilization_ret_min: float = -0.0025
    max_volume_z: float = 2.75
    risk_window: int = 20
    max_spy_loss_5d: float = -0.045
    max_hyg_loss_5d: float = -0.035
    min_history: int = 80
    gross: float = 1.0
    tlt_weight: float = 0.55
    ief_weight: float = 0.30
    tip_weight: float = 0.15
    shy_fallback_weight: float = 1.0


PARAMS = Params()


def _zero(symbols: list[str]) -> dict[str, float]:
    return {s: 0.0 for s in symbols}


def _wide(prices: pd.DataFrame, symbols: list[str]) -> dict[str, pd.DataFrame] | None:
    px = prices[prices["symbol"].isin(symbols)].copy()
    if px.empty:
        return None
    px["timestamp"] = pd.to_datetime(px["timestamp"], utc=True)
    px = px.sort_values(["timestamp", "symbol"])
    return {c: px.pivot(index="timestamp", columns="symbol", values=c).sort_index().ffill() for c in ("open", "high", "low", "close", "volume")}


def _nth_weekday(year: int, month: int, weekday: int, n: int, tz=None) -> pd.Timestamp:
    d = pd.Timestamp(year=year, month=month, day=1, tz=tz)
    return d + pd.Timedelta(days=((weekday - d.weekday()) % 7) + 7 * (n - 1))


def _last_weekday(year: int, month: int, weekday: int, tz=None) -> pd.Timestamp:
    d = pd.Timestamp(year=year, month=month, day=1, tz=tz) + pd.offsets.MonthEnd(0)
    return d - pd.Timedelta(days=(d.weekday() - weekday) % 7)


def event_labels(ts: pd.Timestamp) -> set[str]:
    """Deterministic auction/refunding supply labels for a trading date.

    Approximation: second-week 3y/10y/30y reopenings, last-week 2y/5y/7y coupon
    auctions, and expanded quarterly refunding windows in Feb/May/Aug/Nov.
    """
    d = pd.Timestamp(ts).normalize()
    tz = d.tz
    labels: set[str] = set()
    second_tue = _nth_weekday(d.year, d.month, 1, 2, tz)
    last_tue = _last_weekday(d.year, d.month, 1, tz)
    if 0 <= (d - second_tue).days <= 3 and d.weekday() < 5:
        labels.add("auction")
    if 0 <= (d - last_tue).days <= 3 and d.weekday() < 5:
        labels.add("auction")
    if d.month in {2, 5, 8, 11}:
        first_wed = _nth_weekday(d.year, d.month, 2, 1, tz)
        refund_start = first_wed - pd.Timedelta(days=1)
        refund_end = first_wed + pd.Timedelta(days=9)
        if refund_start <= d <= refund_end and d.weekday() < 5:
            labels.add("refunding")
            labels.add("auction")
    return labels


def _is_turn_of_month(index: pd.DatetimeIndex, ts: pd.Timestamp) -> bool:
    loc = index.get_indexer([ts])[0]
    if loc < 0:
        return False
    prev_same = sum(1 for i in range(max(0, loc - 6), loc) if index[i].month == ts.month)
    next_same = sum(1 for i in range(loc + 1, min(len(index), loc + 7)) if index[i].month == ts.month)
    return prev_same <= 2 or next_same == 0


def _allocation(output_symbols: list[str], duration_signal: bool) -> dict[str, float]:
    raw = {s: 0.0 for s in output_symbols}
    if duration_signal:
        for s, w in (("TLT", PARAMS.tlt_weight), ("IEF", PARAMS.ief_weight), ("TIP", PARAMS.tip_weight)):
            if s in raw:
                raw[s] = w * PARAMS.gross
    elif DEFENSIVE_LEG in raw:
        raw[DEFENSIVE_LEG] = 0.0
    gross = sum(abs(v) for v in raw.values())
    if gross > PARAMS.gross and gross > 0:
        raw = {s: v / gross * PARAMS.gross for s, v in raw.items()}
    return raw


def generate_signals(context) -> dict[str, float]:
    output_symbols = list(getattr(context, "symbols", []) or [])
    symbols = [s for s in output_symbols if s in SELECTED_UNIVERSE]
    prices = getattr(context, "prices", pd.DataFrame())
    if prices.empty or not {"TLT", "IEF", "SHY"}.issubset(set(symbols)):
        return _zero(output_symbols)
    wide = _wide(prices, symbols)
    if wide is None:
        return _zero(output_symbols)
    close = wide["close"]
    if len(close) < PARAMS.min_history:
        return _zero(output_symbols)
    tradable = [s for s in symbols if s in close.columns and pd.notna(close[s].iloc[-1])]
    if not {"TLT", "IEF", "SHY"}.issubset(tradable):
        return _zero(output_symbols)
    close = close[tradable]
    as_of = close.index[-1]
    if not event_labels(as_of):
        return _zero(output_symbols)

    ret = close.pct_change()
    rel5 = close[["TLT", "IEF"]].pct_change(PARAMS.lookback).mean(axis=1) - close["SHY"].pct_change(PARAMS.lookback)
    tlt_rel5 = close["TLT"].pct_change(PARAMS.lookback) - close["SHY"].pct_change(PARAMS.lookback)
    high = wide["high"][tradable]
    low = wide["low"][tradable]
    vol = wide["volume"][tradable]
    rng = (high - low).replace(0.0, pd.NA)
    clv = ((close - low) / rng).clip(0.0, 1.0)
    vol_mean = vol.shift(1).rolling(60, min_periods=40).mean()
    vol_std = vol.shift(1).rolling(60, min_periods=40).std().replace(0.0, pd.NA)
    vol_z = ((vol - vol_mean) / vol_std).replace([float("inf"), float("-inf")], pd.NA)

    latest = close.index[-1]
    needed = [rel5.loc[latest], tlt_rel5.loc[latest], clv.loc[latest, "TLT"], ret.loc[latest, "TLT"], vol_z.loc[latest, "TLT"]]
    if not all(pd.notna(x) and math.isfinite(float(x)) for x in needed):
        return _zero(output_symbols)
    if "SPY" in close and close["SPY"].pct_change(5).loc[latest] <= PARAMS.max_spy_loss_5d:
        return _zero(output_symbols)
    if "HYG" in close and close["HYG"].pct_change(5).loc[latest] <= PARAMS.max_hyg_loss_5d:
        return _zero(output_symbols)

    concession = float(rel5.loc[latest]) <= PARAMS.min_duration_concession and float(tlt_rel5.loc[latest]) <= PARAMS.min_tlt_concession
    stabilized = (float(clv.loc[latest, "TLT"]) >= PARAMS.stabilization_clv_min and float(ret.loc[latest, "TLT"]) >= PARAMS.stabilization_ret_min and float(vol_z.loc[latest, "TLT"]) <= PARAMS.max_volume_z)
    return _allocation(output_symbols, concession and stabilized)
