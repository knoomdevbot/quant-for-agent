"""Timestamp-safe tax-loss rebound basket with ETF and large-cap sleeves.

qfa-compatible alpha model exposing generate_signals(context). The model is
long-only and active only on the last December trading day and the first N
January trading days. It ranks predeclared sleeve symbols by YTD return as of
the last trading day on/before Dec 20 and buys the worst performers.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception:  # pragma: no cover - PyYAML may be absent in minimal qfa envs
    yaml = None


DEFAULT_CONFIG: dict[str, Any] = {
    "parameters": {
        "signal_day_cutoff": 20,
        "primary_hold_january_trading_days": 5,
        "loser_fraction": 0.25,
        "min_losers_per_sleeve": 3,
        "max_losers_per_sleeve": 8,
        "sleeve_weights": {"etf": 0.5, "equity": 0.5},
    },
    "universe_candidates": {"etf": {"symbols": []}, "equity": {"symbols": []}},
}


def _load_config() -> dict[str, Any]:
    path = Path(__file__).with_name("config.yaml")
    if not path.exists():
        return DEFAULT_CONFIG
    text = path.read_text(encoding="utf-8")
    if yaml is not None:
        cfg = yaml.safe_load(text) or {}
    else:
        # Final artifact is written as JSON-compatible YAML so the model has no
        # hard dependency on PyYAML in minimal qfa environments.
        try:
            cfg = json.loads(text)
        except json.JSONDecodeError:
            cfg = {}
    merged = DEFAULT_CONFIG.copy()
    merged.update(cfg)
    return merged


CONFIG = _load_config()
PARAMS = CONFIG.get("parameters", {})
ETF_SYMBOLS = set(CONFIG.get("selected_universe", {}).get("etf", []) or CONFIG.get("universe_candidates", {}).get("etf", {}).get("symbols", []))
EQUITY_SYMBOLS = set(CONFIG.get("selected_universe", {}).get("equity", []) or CONFIG.get("universe_candidates", {}).get("equity", {}).get("symbols", []))


def _symbol_close_matrix(prices):
    frame = prices.copy()
    frame["timestamp"] = frame["timestamp"].dt.tz_localize(None) if getattr(frame["timestamp"].dt, "tz", None) is not None else frame["timestamp"]
    frame["date"] = frame["timestamp"].dt.normalize()
    return frame.pivot_table(index="date", columns="symbol", values="close", aggfunc="last").sort_index()


def _event_state(as_of, close):
    as_of = as_of.tz_localize(None) if getattr(as_of, "tzinfo", None) is not None else as_of
    current_date = as_of.normalize()
    year = int(current_date.year)
    dec_dates = close.index[(close.index.year == year) & (close.index.month == 12)]
    jan_dates = close.index[(close.index.year == year) & (close.index.month == 1)]
    hold_n = int(PARAMS.get("primary_hold_january_trading_days", 5))
    if len(dec_dates) and current_date == dec_dates.max():
        return year, current_date
    if len(jan_dates):
        first_jan_hold = list(jan_dates[:hold_n])
        if current_date in first_jan_hold:
            return year - 1, current_date
    return None, current_date


def _sleeve_losers(close, event_year: int, symbols: set[str]) -> list[str]:
    if not symbols:
        return []
    cutoff = int(PARAMS.get("signal_day_cutoff", 20))
    ytd = close.loc[(close.index.year == event_year) & (close.index.month <= 12)]
    if ytd.empty:
        return []
    signal_dates = ytd.index[(ytd.index.month < 12) | ((ytd.index.month == 12) & (ytd.index.day <= cutoff))]
    if len(signal_dates) == 0:
        return []
    signal_date = signal_dates.max()
    year_start = ytd.index.min()
    cols = [s for s in sorted(symbols) if s in close.columns]
    returns = {}
    for symbol in cols:
        start_price = close.at[year_start, symbol] if year_start in close.index else math.nan
        end_price = close.at[signal_date, symbol]
        if start_price and not math.isnan(start_price) and not math.isnan(end_price):
            returns[symbol] = float(end_price / start_price - 1.0)
    if not returns:
        return []
    loser_fraction = float(PARAMS.get("loser_fraction", 0.25))
    min_losers = int(PARAMS.get("min_losers_per_sleeve", 3))
    max_losers = int(PARAMS.get("max_losers_per_sleeve", 8))
    count = max(min_losers, math.ceil(len(returns) * loser_fraction))
    count = min(max_losers, count, len(returns))
    return [symbol for symbol, _ in sorted(returns.items(), key=lambda item: (item[1], item[0]))[:count]]


def generate_signals(context):
    if context.prices is None or len(context.prices) == 0:
        return {symbol: 0.0 for symbol in context.symbols}
    close = _symbol_close_matrix(context.prices)
    event_year, _ = _event_state(context.as_of, close)
    if event_year is None:
        return {symbol: 0.0 for symbol in context.symbols}
    sleeve_weights = PARAMS.get("sleeve_weights", {"etf": 0.5, "equity": 0.5})
    signals = {symbol: 0.0 for symbol in context.symbols}
    for sleeve_name, symbols in (("etf", ETF_SYMBOLS), ("equity", EQUITY_SYMBOLS)):
        losers = [s for s in _sleeve_losers(close, event_year, symbols) if s in signals]
        if not losers:
            continue
        sleeve_weight = float(sleeve_weights.get(sleeve_name, 0.0))
        per_symbol = sleeve_weight / len(losers)
        for symbol in losers:
            signals[symbol] = signals.get(symbol, 0.0) + per_symbol
    return signals
