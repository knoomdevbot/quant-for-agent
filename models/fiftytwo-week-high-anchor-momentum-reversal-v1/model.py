"""Lagged 52-week-high anchored momentum/reversal split model.

Research-only qfa model for AR-128. Uses daily OHLCV supplied in
context.prices; does not fetch data, read CSVs, start daemons, or place orders.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd

EQUITIES = (
    "AAPL","MSFT","NVDA","AMZN","META","GOOGL","GOOG","AVGO","TSLA","BRK.B",
    "JPM","LLY","V","XOM","UNH","MA","COST","NFLX","WMT","HD","PG","JNJ",
    "ABBV","BAC","KO","CRM","ORCL","MRK","CVX","AMD","PEP","TMO","LIN","MCD",
    "CSCO","ABT","ACN","WFC","DIS","IBM","GE","PM","NOW","QCOM","TXN","VZ",
    "INTU","AMAT","CAT","ISRG","PFE","RTX","NEE","SPGI","GS","UBER","LOW",
    "HON","BKNG","UNP","BLK","T","TJX","SYK","ETN","SCHW","LMT","DE","ADBE",
    "PANW","VRTX","CB","MDT","ADI","MMC","PLD","AMGN","GILD","SBUX","C",
)

ETFS = (
    "SPY","QQQ","IWM","DIA","RSP","VTI","VEA","VWO","EFA","EEM","IYR","VNQ",
    "XLF","XLK","XLY","XLP","XLE","XLI","XLV","XLU","XLB","XLC","SMH","IBB",
    "TLT","IEF","SHY","IEI","HYG","LQD","TIP","BIL","GLD","SLV","USO","DBA",
    "DBC","UUP","FXE","FXY","EWA","EWC","EWJ","EWG","EWU","EWW","EWZ","INDA",
)

@dataclass(frozen=True)
class Params:
    high_low_window: int = 252
    momentum_window: int = 126
    vol_window: int = 63
    top_equities: int = 15
    short_equities: int = 8
    top_etfs: int = 8
    short_etfs: int = 4
    min_history: int = 253
    gross_exposure: float = 1.0
    max_abs_weight: float = 0.08
    high_proximity_floor: float = 0.92
    low_proximity_ceiling: float = 1.12

PARAMS = Params()


def _zero(symbols: list[str]) -> dict[str, float]:
    return {s: 0.0 for s in symbols}


def _normalize(raw: dict[str, float], symbols: list[str]) -> dict[str, float]:
    clean = {s: float(v) for s, v in raw.items() if math.isfinite(float(v)) and abs(float(v)) > 0}
    if not clean:
        return _zero(symbols)
    gross = sum(abs(v) for v in clean.values())
    scaled = {s: v / gross * PARAMS.gross_exposure for s, v in clean.items()}
    capped = {s: max(min(scaled.get(s, 0.0), PARAMS.max_abs_weight), -PARAMS.max_abs_weight) for s in symbols}
    gross2 = sum(abs(v) for v in capped.values())
    if gross2 <= 0:
        return _zero(symbols)
    mult = min(1.0, PARAMS.gross_exposure / gross2)
    return {s: float(capped.get(s, 0.0) * mult) for s in symbols}


def _sleeve_scores(close: pd.DataFrame, high: pd.DataFrame, low: pd.DataFrame, symbols: list[str], top_n: int, short_n: int) -> dict[str, float]:
    if len(close) < PARAMS.min_history:
        return {}
    tradable = [s for s in symbols if s in close.columns]
    if len(tradable) < max(5, min(top_n, len(symbols) // 4)):
        return {}
    c = close[tradable]
    h = high[tradable]
    low_prices = low[tradable]
    last = c.iloc[-1]
    # Strictly lagged 252-day extrema exclude the current bar.
    lag_high = h.iloc[:-1].tail(PARAMS.high_low_window).max()
    lag_low = low_prices.iloc[:-1].tail(PARAMS.high_low_window).min()
    mom = last / c.shift(PARAMS.momentum_window).iloc[-1] - 1.0
    vol = c.pct_change().tail(PARAMS.vol_window).std(ddof=1).replace(0.0, pd.NA)
    prox_high = (last / lag_high).replace([float("inf"), float("-inf")], pd.NA)
    prox_low = (last / lag_low).replace([float("inf"), float("-inf")], pd.NA)

    df = pd.DataFrame({"prox_high": prox_high, "prox_low": prox_low, "mom": mom, "vol": vol}).dropna()
    if df.empty:
        return {}
    df["high_rank"] = df["prox_high"].rank(pct=True)
    df["mom_rank"] = df["mom"].rank(pct=True)
    df["vol_rank"] = df["vol"].rank(pct=True)
    df["score"] = 0.55 * df["high_rank"] + 0.35 * df["mom_rank"] - 0.10 * df["vol_rank"]
    long_df = df[(df["prox_high"] >= PARAMS.high_proximity_floor) & (df["mom"] > 0)].sort_values("score", ascending=False).head(top_n)

    # Diagnostic underweight: near the lagged low and still in negative medium-term trend.
    low_df = df[(df["prox_low"] <= PARAMS.low_proximity_ceiling) & (df["mom"] < 0)].sort_values("score", ascending=True).head(short_n)
    raw = {s: 1.0 for s in long_df.index}
    raw.update({s: -0.5 for s in low_df.index if s not in raw})
    return raw


def generate_signals(context) -> dict[str, float]:
    output_symbols = list(getattr(context, "symbols", []) or [])
    prices = getattr(context, "prices", pd.DataFrame())
    if not output_symbols or prices is None or prices.empty:
        return _zero(output_symbols)
    required = {"timestamp", "symbol", "close", "high", "low"}
    if not required.issubset(prices.columns):
        return _zero(output_symbols)
    px = prices[prices["symbol"].isin(output_symbols)].copy()
    px["timestamp"] = pd.to_datetime(px["timestamp"], utc=True)
    close = px.pivot(index="timestamp", columns="symbol", values="close").sort_index().ffill()
    high = px.pivot(index="timestamp", columns="symbol", values="high").sort_index().ffill()
    low = px.pivot(index="timestamp", columns="symbol", values="low").sort_index().ffill()

    eq_symbols = [s for s in output_symbols if s in EQUITIES]
    etf_symbols = [s for s in output_symbols if s in ETFS]
    raw: dict[str, float] = {}
    raw.update(_sleeve_scores(close, high, low, eq_symbols, PARAMS.top_equities, PARAMS.short_equities))
    etf_raw = _sleeve_scores(close, high, low, etf_symbols, PARAMS.top_etfs, PARAMS.short_etfs)
    # Keep ETF sleeve separate and lower capital share as redundancy stress test.
    raw.update({s: 0.75 * v for s, v in etf_raw.items()})
    return _normalize(raw, output_symbols)
