"""AR-106 ETF OPEX/rebalance liquidity-pressure reversal.

Research-only qfa alpha. Uses only completed daily OHLCV bars supplied by
qfa/Alpaca. Signals are strictly gated to predeclared option-expiry and quarterly
rebalance weeks, excluding standard turn-of-month windows by default, and take
short-horizon contrarian ETF exposure after abnormal-volume close-location
pressure with failed follow-through confirmation.
"""

from __future__ import annotations

import math

import pandas as pd

UNIVERSE = (
    "SPY", "QQQ", "IWM", "DIA", "VTI",
    "XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE",
    "IWF", "IWD", "MTUM", "VLUE", "QUAL", "USMV",
    "TLT", "IEF", "SHY", "HYG", "LQD",
    "GLD", "SLV", "USO", "DBA",
)


class Params:
    volume_window: int = 60
    vol_z_min: float = 1.15
    clv_extreme: float = 0.78
    event_ret_min: float = 0.004
    fail_follow_max: float = 0.003
    realized_vol_window: int = 20
    max_realized_vol: float = 0.55
    max_symbol_weight: float = 0.10
    min_symbols: int = 20
    exclude_turn_of_month: bool = True


PARAMS = Params()


def _zero(symbols: list[str]) -> dict[str, float]:
    return {s: 0.0 for s in symbols}


def _third_friday(ts: pd.Timestamp) -> pd.Timestamp:
    first = pd.Timestamp(year=ts.year, month=ts.month, day=1, tz=ts.tz)
    offset = (4 - first.weekday()) % 7
    return first + pd.Timedelta(days=offset + 14)


def _is_opex_or_rebalance_week(ts: pd.Timestamp) -> bool:
    d = pd.Timestamp(ts).normalize()
    tf = _third_friday(d)
    # Monday-Friday of monthly OPEX week; quarterly OPEX/rebalance uses same gate.
    return abs((d - tf).days) <= 4 and d.weekday() < 5


def _is_turn_of_month(index: pd.DatetimeIndex, ts: pd.Timestamp) -> bool:
    loc = index.get_indexer([ts])[0]
    if loc < 0:
        return False
    month = ts.month
    prev_same = sum(1 for i in range(max(0, loc - 6), loc) if index[i].month == month)
    next_same = sum(1 for i in range(loc + 1, min(len(index), loc + 7)) if index[i].month == month)
    # standard ToM: last 1 business day of prior month through first 3 of new month.
    return prev_same <= 2 or next_same == 0


def _wide(prices: pd.DataFrame, symbols: list[str]) -> dict[str, pd.DataFrame] | None:
    px = prices[prices["symbol"].isin(symbols)].copy()
    if px.empty:
        return None
    px["timestamp"] = pd.to_datetime(px["timestamp"], utc=True)
    px = px.sort_values(["timestamp", "symbol"])
    return {c: px.pivot(index="timestamp", columns="symbol", values=c).sort_index().ffill() for c in ("open", "high", "low", "close", "volume")}


def _normalize(raw: dict[str, float]) -> dict[str, float]:
    clean = {s: max(-PARAMS.max_symbol_weight, min(PARAMS.max_symbol_weight, float(w))) for s, w in raw.items() if math.isfinite(float(w))}
    gross = sum(abs(w) for w in clean.values())
    if gross <= 0:
        return {s: 0.0 for s in raw}
    return {s: float(clean.get(s, 0.0) / gross) for s in raw}


def generate_signals(context) -> dict[str, float]:
    output_symbols = list(getattr(context, "symbols", []) or [])
    symbols = [s for s in output_symbols if s in UNIVERSE]
    prices = getattr(context, "prices", pd.DataFrame())
    if prices.empty or len(symbols) < PARAMS.min_symbols:
        return _zero(output_symbols)
    wide = _wide(prices, symbols)
    if wide is None:
        return _zero(output_symbols)
    close_all = wide["close"]
    latest_row = close_all.iloc[-1]
    min_obs = max(PARAMS.volume_window + 5, int(len(close_all) * 0.90))
    close = close_all[[s for s in symbols if s in close_all.columns and pd.notna(latest_row.get(s)) and int(close_all[s].count()) >= min_obs]]
    tradable = [s for s in symbols if s in close.columns]
    if len(tradable) < PARAMS.min_symbols or len(close) < PARAMS.volume_window + 5:
        return _zero(output_symbols)
    as_of = close.index[-1]
    if not _is_opex_or_rebalance_week(as_of):
        return _zero(output_symbols)
    if PARAMS.exclude_turn_of_month and _is_turn_of_month(close.index, as_of):
        return _zero(output_symbols)

    high, low, volume = wide["high"][tradable], wide["low"][tradable], wide["volume"][tradable]
    close = close[tradable]
    day_range = (high - low).replace(0.0, pd.NA)
    clv = ((close - low) / day_range).clip(0.0, 1.0)
    ret1 = close.pct_change()
    ret3 = close.pct_change(3)
    fwd_fail = ret1
    vol_mean = volume.shift(1).rolling(PARAMS.volume_window, min_periods=PARAMS.volume_window).mean()
    vol_std = volume.shift(1).rolling(PARAMS.volume_window, min_periods=PARAMS.volume_window).std().replace(0.0, pd.NA)
    vol_z = ((volume - vol_mean) / vol_std).replace([float("inf"), float("-inf")], pd.NA)
    rv = ret1.shift(1).rolling(PARAMS.realized_vol_window, min_periods=PARAMS.realized_vol_window).std() * (252 ** 0.5)

    latest = close.index[-1]
    raw = {s: 0.0 for s in output_symbols}
    for s in tradable:
        if not all(pd.notna(x) for x in [vol_z.loc[latest, s], clv.loc[latest, s], rv.loc[latest, s], ret3.loc[latest, s]]):
            continue
        if float(rv.loc[latest, s]) > PARAMS.max_realized_vol or float(vol_z.loc[latest, s]) < PARAMS.vol_z_min:
            continue
        pressure_up = float(clv.loc[latest, s]) >= PARAMS.clv_extreme and float(ret3.loc[latest, s]) >= PARAMS.event_ret_min and float(fwd_fail.loc[latest, s]) <= PARAMS.fail_follow_max
        pressure_down = float(clv.loc[latest, s]) <= 1.0 - PARAMS.clv_extreme and float(ret3.loc[latest, s]) <= -PARAMS.event_ret_min and float(fwd_fail.loc[latest, s]) >= -PARAMS.fail_follow_max
        if pressure_up:
            raw[s] = -min(1.0, (float(vol_z.loc[latest, s]) - PARAMS.vol_z_min + 0.25) / 3.0) / max(float(rv.loc[latest, s]), 0.05)
        elif pressure_down:
            raw[s] = min(1.0, (float(vol_z.loc[latest, s]) - PARAMS.vol_z_min + 0.25) / 3.0) / max(float(rv.loc[latest, s]), 0.05)
    return _normalize(raw)
