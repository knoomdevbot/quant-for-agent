"""
AR-107 research model: post-drawdown stabilized single-name sector-residual defensive leadership.

QFA contract: expose generate_signals(context) -> dict[str, float].  The model uses
only historical OHLCV bars supplied in context.prices (normally qfa/Alpaca real daily
bars).  It is research-only and never places orders.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

SECTOR_ETF = {
    # Technology / communication
    "AAPL": "XLK", "MSFT": "XLK", "NVDA": "XLK", "AVGO": "XLK", "ORCL": "XLK", "CRM": "XLK", "ADBE": "XLK", "AMD": "XLK", "CSCO": "XLK", "ACN": "XLK", "QCOM": "XLK", "TXN": "XLK", "INTU": "XLK", "AMAT": "XLK", "NOW": "XLK", "MU": "XLK", "LRCX": "XLK", "INTC": "XLK", "IBM": "XLK",
    "GOOGL": "XLC", "GOOG": "XLC", "META": "XLC", "NFLX": "XLC", "CMCSA": "XLC", "DIS": "XLC", "TMUS": "XLC", "VZ": "XLC", "T": "XLC",
    # Consumer discretionary / staples
    "AMZN": "XLY", "TSLA": "XLY", "HD": "XLY", "MCD": "XLY", "NKE": "XLY", "SBUX": "XLY", "LOW": "XLY", "BKNG": "XLY", "TJX": "XLY", "CMG": "XLY", "GM": "XLY", "F": "XLY",
    "WMT": "XLP", "COST": "XLP", "PG": "XLP", "KO": "XLP", "PEP": "XLP", "PM": "XLP", "MO": "XLP", "CL": "XLP", "MDLZ": "XLP", "TGT": "XLP",
    # Healthcare
    "LLY": "XLV", "UNH": "XLV", "JNJ": "XLV", "MRK": "XLV", "ABBV": "XLV", "ABT": "XLV", "TMO": "XLV", "DHR": "XLV", "PFE": "XLV", "AMGN": "XLV", "ISRG": "XLV", "GILD": "XLV", "BMY": "XLV", "CVS": "XLV", "MDT": "XLV",
    # Financials
    "BRK.B": "XLF", "JPM": "XLF", "V": "XLF", "MA": "XLF", "BAC": "XLF", "WFC": "XLF", "GS": "XLF", "MS": "XLF", "AXP": "XLF", "C": "XLF", "BLK": "XLF", "SCHW": "XLF", "PGR": "XLF", "CB": "XLF",
    # Industrials / materials / energy / utilities / real estate
    "GE": "XLI", "CAT": "XLI", "RTX": "XLI", "HON": "XLI", "UNP": "XLI", "BA": "XLI", "UPS": "XLI", "DE": "XLI", "LMT": "XLI", "ADP": "XLI", "ETN": "XLI",
    "LIN": "XLB", "APD": "XLB", "SHW": "XLB", "ECL": "XLB", "NEM": "XLB", "FCX": "XLB", "DOW": "XLB", "DD": "XLB",
    "XOM": "XLE", "CVX": "XLE", "COP": "XLE", "SLB": "XLE", "EOG": "XLE", "MPC": "XLE", "PSX": "XLE", "OXY": "XLE",
    "NEE": "XLU", "SO": "XLU", "DUK": "XLU", "AEP": "XLU", "SRE": "XLU", "EXC": "XLU", "D": "XLU",
    "PLD": "XLRE", "AMT": "XLRE", "EQIX": "XLRE", "WELL": "XLRE", "SPG": "XLRE", "O": "XLRE",
}

SECTOR_ETFS = sorted(set(SECTOR_ETF.values()))
SINGLE_NAMES = sorted(SECTOR_ETF)
SYMBOLS = SINGLE_NAMES + ["SPY"] + SECTOR_ETFS


def _pivot(prices: pd.DataFrame, field: str) -> pd.DataFrame:
    df = prices.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df.pivot(index="timestamp", columns="symbol", values=field).sort_index().ffill()


def _rank01(s: pd.Series) -> pd.Series:
    if s.empty:
        return s
    return s.rank(pct=True).fillna(0.5)


def generate_signals(context: Any) -> dict[str, float]:
    symbols = [s for s in getattr(context, "symbols", SYMBOLS) if s in SINGLE_NAMES]
    if not symbols:
        return {}
    prices = getattr(context, "prices", None)
    if prices is None or len(prices) < 180:
        return {s: 0.0 for s in symbols}

    close = _pivot(prices, "close")
    volume = _pivot(prices, "volume") if "volume" in prices.columns else close * np.nan
    if "SPY" not in close or len(close) < 180:
        return {s: 0.0 for s in symbols}
    rets = close.pct_change()
    spy = close["SPY"]
    spy_dd = spy / spy.rolling(126).max() - 1.0
    # Only activate after a meaningful market drawdown has stopped making fresh lows.
    recent_min = spy_dd.rolling(10).min().iloc[-1]
    prior_min = spy_dd.rolling(10).min().shift(5).iloc[-1]
    drawdown_active = bool(spy_dd.iloc[-1] < -0.035 and recent_min >= prior_min - 0.002)
    if not drawdown_active:
        return {s: 0.0 for s in symbols}

    rows = []
    market = rets["SPY"]
    for s in symbols:
        etf = SECTOR_ETF.get(s)
        if s not in close or etf not in close:
            continue
        r = rets[s].dropna()
        if len(r) < 126:
            continue
        resid = rets[s] - 0.45 * market - 0.55 * rets[etf]
        mom20 = (1.0 + resid.tail(20).fillna(0.0)).prod() - 1.0
        mom60 = (1.0 + resid.tail(60).fillna(0.0)).prod() - 1.0
        vol = float(r.tail(63).std() * math.sqrt(252))
        beta = float(r.tail(126).cov(market.tail(126)) / (market.tail(126).var() + 1e-12))
        rel_vol = float((volume[s].tail(20).mean() / (volume[s].tail(60).mean() + 1e-12)) if s in volume else 1.0)
        breadth = float((resid.tail(20) > 0).mean())
        if not np.isfinite([mom20, mom60, vol, beta, rel_vol, breadth]).all():
            continue
        if vol > 0.58 or beta > 1.55 or close[s].iloc[-1] < 10:
            continue
        rows.append((s, etf, mom20, mom60, vol, beta, rel_vol, breadth))
    if len(rows) < 10:
        return {s: 0.0 for s in symbols}
    df = pd.DataFrame(rows, columns=["symbol", "sector", "mom20", "mom60", "vol", "beta", "rel_vol", "breadth"]).set_index("symbol")
    score = 0.48 * _rank01(df["mom20"]) + 0.28 * _rank01(df["mom60"]) + 0.14 * _rank01(df["breadth"]) + 0.10 * _rank01(df["rel_vol"])
    # Defensive variables are only brakes/tie-breakers.
    score = score - 0.08 * _rank01(df["beta"]) - 0.06 * _rank01(df["vol"])
    leaders = score.sort_values(ascending=False).head(15)
    if leaders.empty:
        return {s: 0.0 for s in symbols}
    raw = leaders.clip(lower=0.0)
    if raw.sum() <= 0:
        raw = pd.Series(1.0, index=leaders.index)
    weights = (raw / raw.sum()).clip(upper=0.09)
    # Sector cap 28%; redistribute excess once to uncapped names.
    for sec in sorted(df.loc[weights.index, "sector"].unique()):
        idx = [s for s in weights.index if df.loc[s, "sector"] == sec]
        subtotal = float(weights.loc[idx].sum())
        if subtotal > 0.28:
            weights.loc[idx] *= 0.28 / subtotal
    weights = weights / weights.sum() if weights.sum() > 0 else weights
    weights = (0.95 * weights).to_dict()
    return {s: float(weights.get(s, 0.0)) for s in symbols}
