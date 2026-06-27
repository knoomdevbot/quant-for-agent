from __future__ import annotations

from datetime import timedelta

CONFIG = {
    "selected_universe": ["IJR", "IWB", "IWD", "IWF", "IWM", "IWN", "IWO", "MDY", "VBR", "VBK", "VTI", "VTWO"],
    "pre_event_pressure_lookback_trading_days": 5,
    "holding_period_trading_days": 5,
    "sleeves": [
        {"name": "russell_small_vs_large", "small": "IWM", "large": "IWB"},
        {"name": "vanguard_russell2000_vs_total_market", "small": "VTWO", "large": "VTI"},
        {"name": "core_small_vs_mid", "small": "IJR", "large": "MDY"},
        {"name": "small_value_vs_large_value", "small": "IWN", "large": "IWD"},
        {"name": "small_growth_vs_large_growth", "small": "IWO", "large": "IWF"},
        {"name": "vanguard_small_growth_vs_small_value", "small": "VBK", "large": "VBR"},
    ],
}


def _last_friday_in_june(year: int):
    import calendar
    from datetime import date
    last_day = date(year, 6, calendar.monthrange(year, 6)[1])
    return last_day - timedelta(days=(last_day.weekday() - 4) % 7)


def _wide_close(prices):
    df = prices.copy()
    if df.empty:
        return None
    df["timestamp"] = __import__("pandas").to_datetime(df["timestamp"], utc=True)
    return df.pivot_table(index="timestamp", columns="symbol", values="close", aggfunc="last").sort_index().ffill()


def generate_signals(context):
    """Annual Russell-reconstitution proxy reversal.

    Cash except for the 5 trading days after the last Friday in June. During that
    hold, reverse each selected size/style spread's 5-trading-day pre-event move.
    """
    pd = __import__("pandas")
    as_of = pd.Timestamp(context.as_of).tz_convert("UTC") if pd.Timestamp(context.as_of).tzinfo else pd.Timestamp(context.as_of, tz="UTC")
    event_day = pd.Timestamp(_last_friday_in_june(as_of.year), tz="UTC")
    close = _wide_close(context.prices)
    if close is None or close.empty:
        return {}
    dates = list(close.index)
    event_candidates = [d for d in dates if d.date() <= event_day.date()]
    if not event_candidates:
        return {}
    event_ts = event_candidates[-1]
    try:
        event_idx = dates.index(event_ts)
        asof_idx = dates.index(as_of)
    except ValueError:
        return {}
    entry_idx = event_idx + 1
    exit_idx = event_idx + 1 + CONFIG["holding_period_trading_days"]
    if not (entry_idx <= asof_idx < exit_idx):
        return {symbol: 0.0 for symbol in context.symbols}
    lookback = CONFIG["pre_event_pressure_lookback_trading_days"]
    if event_idx - lookback < 0:
        return {symbol: 0.0 for symbol in context.symbols}
    start = close.iloc[event_idx - lookback]
    end = close.iloc[event_idx]
    weights = {symbol: 0.0 for symbol in context.symbols}
    active = 0
    for sleeve in CONFIG["sleeves"]:
        small, large = sleeve["small"], sleeve["large"]
        if small not in close.columns or large not in close.columns or small not in context.symbols or large not in context.symbols:
            continue
        if not all(pd.notna([start.get(small), start.get(large), end.get(small), end.get(large)])):
            continue
        spread = (float(end[small]) / float(start[small]) - 1.0) - (float(end[large]) / float(start[large]) - 1.0)
        direction = -1.0 if spread > 0 else 1.0  # reverse small-minus-large pressure
        weights[small] += direction
        weights[large] -= direction
        active += 1
    if active == 0:
        return {symbol: 0.0 for symbol in context.symbols}
    gross = sum(abs(v) for v in weights.values())
    return {symbol: value / gross for symbol, value in weights.items()}
