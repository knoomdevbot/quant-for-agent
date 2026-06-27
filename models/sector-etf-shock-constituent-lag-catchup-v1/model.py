"""Sector ETF shock lead-lag catch-up alpha.

QFA contract: expose generate_signals(context) -> dict[str, float].
Research-only model using only daily OHLCV bars supplied in context.prices.
No daemon, orders, CSV input, or persistent raw data are used by this module.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

SECTOR_ETFS: dict[str, str] = {
    "AAPL": "XLK", "MSFT": "XLK", "NVDA": "XLK", "AVGO": "XLK", "ORCL": "XLK", "ADBE": "XLK",
    "CRM": "XLK", "AMD": "XLK", "INTC": "XLK", "QCOM": "XLK", "TXN": "XLK", "IBM": "XLK",
    "AMZN": "XLY", "TSLA": "XLY", "HD": "XLY", "MCD": "XLY", "NKE": "XLY", "SBUX": "XLY",
    "LOW": "XLY", "TJX": "XLY", "BKNG": "XLY", "CMG": "XLY",
    "META": "XLC", "GOOGL": "XLC", "GOOG": "XLC", "NFLX": "XLC", "DIS": "XLC", "CMCSA": "XLC", "VZ": "XLC", "T": "XLC",
    "JPM": "XLF", "BAC": "XLF", "WFC": "XLF", "GS": "XLF", "MS": "XLF", "BLK": "XLF", "AXP": "XLF", "C": "XLF",
    "UNH": "XLV", "JNJ": "XLV", "LLY": "XLV", "ABBV": "XLV", "MRK": "XLV", "TMO": "XLV", "ABT": "XLV", "DHR": "XLV", "PFE": "XLV", "ISRG": "XLV",
    "XOM": "XLE", "CVX": "XLE", "COP": "XLE", "SLB": "XLE", "EOG": "XLE", "MPC": "XLE", "PSX": "XLE",
    "PG": "XLP", "COST": "XLP", "KO": "XLP", "PEP": "XLP", "WMT": "XLP", "PM": "XLP", "MO": "XLP", "MDLZ": "XLP", "CL": "XLP",
    "CAT": "XLI", "GE": "XLI", "HON": "XLI", "UNP": "XLI", "RTX": "XLI", "UPS": "XLI", "BA": "XLI", "DE": "XLI", "LMT": "XLI", "ETN": "XLI",
    "NEE": "XLU", "DUK": "XLU", "SO": "XLU", "AEP": "XLU", "EXC": "XLU", "SRE": "XLU",
    "LIN": "XLB", "APD": "XLB", "SHW": "XLB", "FCX": "XLB", "ECL": "XLB", "NEM": "XLB", "DD": "XLB",
    "PLD": "XLRE", "AMT": "XLRE", "EQIX": "XLRE", "WELL": "XLRE", "SPG": "XLRE", "PSA": "XLRE",
}

CONTROLS = {"SPY", "QQQ", "IWM"}
MIN_BARS = 80
VOL_LOOKBACK = 20
SHOCK_Z = 0.75
TOP_FRACTION = 0.20
MAX_GROSS_PER_SECTOR = 0.25


def _pivot_close(prices: pd.DataFrame) -> pd.DataFrame:
    frame = prices.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    return frame.pivot_table(index="timestamp", columns="symbol", values="close", aggfunc="last").sort_index().ffill()


def _cap_sector_gross(weights: dict[str, float]) -> dict[str, float]:
    capped = dict(weights)
    sector_gross: dict[str, float] = {}
    for symbol, weight in capped.items():
        sector_gross[SECTOR_ETFS[symbol]] = sector_gross.get(SECTOR_ETFS[symbol], 0.0) + abs(weight)
    for symbol, weight in list(capped.items()):
        sector = SECTOR_ETFS[symbol]
        gross = sector_gross.get(sector, 0.0)
        if gross > MAX_GROSS_PER_SECTOR:
            capped[symbol] = weight * MAX_GROSS_PER_SECTOR / gross
    gross_total = sum(abs(weight) for weight in capped.values())
    return {symbol: weight / gross_total for symbol, weight in capped.items()} if gross_total else {}


def generate_signals(context: Any) -> dict[str, float]:
    """Return next-session target weights from lagged daily sector shock catch-up scores."""
    close = _pivot_close(context.prices)
    if len(close) < MIN_BARS or "SPY" not in close.columns:
        return {}
    symbols = [symbol for symbol in context.symbols if symbol in SECTOR_ETFS and symbol in close.columns]
    sector_etfs = sorted({SECTOR_ETFS[symbol] for symbol in symbols})
    if not symbols or any(etf not in close.columns for etf in sector_etfs):
        return {}

    returns = close.pct_change()
    latest = returns.iloc[-1]
    spy_ret = float(latest.get("SPY", np.nan))
    if not np.isfinite(spy_ret):
        return {}

    sector_residual = {etf: float(latest[etf] - spy_ret) for etf in sector_etfs if np.isfinite(latest.get(etf, np.nan))}
    sector_minus_spy = returns[sector_etfs].sub(returns["SPY"], axis=0)
    shock_vol = sector_minus_spy.rolling(VOL_LOOKBACK).std().iloc[-1]
    recent_constituent = returns[symbols].rolling(5).sum().iloc[-1]

    scores: dict[str, float] = {}
    for symbol in symbols:
        etf = SECTOR_ETFS[symbol]
        shock = sector_residual.get(etf)
        threshold = float(shock_vol.get(etf, np.nan)) * SHOCK_Z
        stock_ret = float(latest.get(symbol, np.nan))
        if shock is None or not np.isfinite(threshold) or abs(shock) <= threshold or not np.isfinite(stock_ret):
            continue
        stock_market_resid = stock_ret - spy_ret
        underreaction = shock - stock_market_resid
        continuation_control = 0.20 * float(recent_constituent.get(symbol, 0.0) or 0.0)
        score = np.sign(shock) * underreaction - continuation_control
        if np.isfinite(score):
            scores[symbol] = float(score)

    if len(scores) < 8:
        return {}
    ordered = sorted(scores, key=lambda symbol: scores[symbol])
    sleeve = max(2, int(round(len(ordered) * TOP_FRACTION)))
    shorts = ordered[:sleeve]
    longs = ordered[-sleeve:]
    weights = {symbol: 0.5 / len(longs) for symbol in longs}
    weights.update({symbol: -0.5 / len(shorts) for symbol in shorts})
    return _cap_sector_gross(weights)
