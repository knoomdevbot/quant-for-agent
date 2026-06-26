"""
Constituent-confirmed sector ETF post-earnings pressure allocator.

Research-only qfa alpha contract: expose generate_signals(context) -> dict[str, float].
Uses only historical daily OHLCV bars supplied by qfa/Alpaca.  The rule is
fixed ex ante: in quarterly reporting-season proxy windows, mapped mega-cap
constituent abnormal-volume, residual-return and close-location breadth must
confirm sector ETF pressure before allocating to sector ETFs.  No orders are
placed by this model.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

SECTOR_CONSTITUENTS: dict[str, tuple[str, ...]] = {
    "XLK": ("AAPL", "MSFT", "NVDA", "AVGO", "AMD", "ORCL", "CRM"),
    "XLY": ("AMZN", "TSLA", "HD", "COST", "NKE", "SBUX"),
    "XLC": ("META", "GOOGL", "NFLX", "DIS", "CMCSA", "TMUS"),
    "XLF": ("JPM", "BAC", "WFC", "GS", "MS", "V", "MA"),
    "XLV": ("LLY", "UNH", "JNJ", "ABBV", "MRK", "PFE"),
    "XLE": ("XOM", "CVX", "COP", "SLB", "EOG"),
    "XLP": ("PG", "KO", "PEP", "WMT", "COST", "MDLZ"),
    "XLI": ("GE", "CAT", "HON", "UNP", "RTX", "BA"),
    "XLU": ("NEE", "SO", "DUK", "AEP", "EXC"),
    "XLRE": ("PLD", "AMT", "EQIX", "WELL", "SPG"),
    "XLB": ("LIN", "SHW", "APD", "FCX", "NEM"),
}
TRADE_ETFS: tuple[str, ...] = tuple(SECTOR_CONSTITUENTS)
DEFENSIVE_SYMBOL = "SHY"
SPY = "SPY"

MIN_HISTORY = 90
VOLUME_LOOKBACK = 40
RESID_LOOKBACK = 63
ETF_LOOKBACK = 5
MAX_ETFS = 4
GROSS_TARGET = 1.0
MIN_CONFIRMATION_SCORE = 0.18
MIN_BREADTH = 0.52


def _is_reporting_window(ts: pd.Timestamp) -> bool:
    month = int(ts.month)
    day = int(ts.day)
    return (month, day) >= (1, 10) and (month, day) <= (2, 15) or \
        (month, day) >= (4, 10) and (month, day) <= (5, 15) or \
        (month, day) >= (7, 10) and (month, day) <= (8, 15) or \
        (month, day) >= (10, 10) and (month, day) <= (11, 15)


def _safe_clv(frame: pd.DataFrame) -> pd.Series:
    rng = (frame["high"] - frame["low"]).replace(0, np.nan)
    return ((frame["close"] - frame["low"]) / rng - 0.5).replace([np.inf, -np.inf], np.nan).fillna(0.0)


def _weights_from_history(prices: pd.DataFrame, as_of: Any | None = None) -> dict[str, float]:
    if prices is None or prices.empty:
        return {}
    bars = prices.copy()
    bars["timestamp"] = pd.to_datetime(bars["timestamp"], utc=True)
    if as_of is not None:
        bars = bars[bars["timestamp"] <= pd.Timestamp(as_of).tz_convert("UTC") if pd.Timestamp(as_of).tzinfo else bars["timestamp"] <= pd.Timestamp(as_of, tz="UTC")]
    if bars.empty:
        return {}
    last_ts = bars["timestamp"].max()
    if not _is_reporting_window(last_ts):
        return {}

    close = bars.pivot(index="timestamp", columns="symbol", values="close").sort_index().ffill()
    high = bars.pivot(index="timestamp", columns="symbol", values="high").sort_index().ffill()
    low = bars.pivot(index="timestamp", columns="symbol", values="low").sort_index().ffill()
    volume = bars.pivot(index="timestamp", columns="symbol", values="volume").sort_index().ffill()
    if len(close) < MIN_HISTORY or SPY not in close:
        return {}
    rets = close.pct_change()
    spy_ret = rets[SPY]
    sector_scores: list[tuple[str, float]] = []
    for etf, names in SECTOR_CONSTITUENTS.items():
        if etf not in close or close[etf].dropna().shape[0] < MIN_HISTORY:
            continue
        available = [s for s in names if s in close and close[s].dropna().shape[0] >= MIN_HISTORY]
        if len(available) < 3:
            continue
        etf_ret = close[etf].pct_change(ETF_LOOKBACK).iloc[-1]
        etf_beta = rets[etf].tail(RESID_LOOKBACK).cov(spy_ret.tail(RESID_LOOKBACK)) / max(spy_ret.tail(RESID_LOOKBACK).var(), 1e-8)
        etf_resid = float(etf_ret - etf_beta * close[SPY].pct_change(ETF_LOOKBACK).iloc[-1])
        signs = []
        vol_flags = []
        clv_flags = []
        contrib = []
        for sym in available:
            r = close[sym].pct_change(ETF_LOOKBACK).iloc[-1]
            beta = rets[sym].tail(RESID_LOOKBACK).cov(spy_ret.tail(RESID_LOOKBACK)) / max(spy_ret.tail(RESID_LOOKBACK).var(), 1e-8)
            resid = float(r - beta * close[SPY].pct_change(ETF_LOOKBACK).iloc[-1])
            vol_hist = volume[sym].tail(VOLUME_LOOKBACK + 1)
            vol_z = float((vol_hist.iloc[-1] / max(vol_hist.iloc[:-1].median(), 1.0)) - 1.0) if len(vol_hist) > VOLUME_LOOKBACK else 0.0
            clv = float(((close[sym].iloc[-1] - low[sym].iloc[-1]) / max(high[sym].iloc[-1] - low[sym].iloc[-1], 1e-8)) - 0.5)
            sg = 1.0 if resid > 0 else -1.0
            signs.append(sg)
            vol_flags.append(vol_z > 0.15)
            clv_flags.append((clv > 0.15 and sg > 0) or (clv < -0.15 and sg < 0))
            contrib.append(sg * min(max(vol_z, 0.0), 2.0) * (0.5 + abs(clv)))
        if not contrib:
            continue
        direction = 1.0 if np.nanmean(contrib) > 0 else -1.0
        breadth = float(np.mean([x == direction for x in signs]))
        vol_breadth = float(np.mean(vol_flags))
        clv_breadth = float(np.mean(clv_flags))
        etf_direction = 1.0 if etf_resid > 0 else -1.0
        if breadth >= MIN_BREADTH and vol_breadth >= 0.35 and clv_breadth >= 0.35 and direction == etf_direction:
            score = abs(float(np.nanmean(contrib))) * breadth * (0.5 + vol_breadth) * (0.5 + clv_breadth)
            if score >= MIN_CONFIRMATION_SCORE:
                sector_scores.append((etf, direction * score))
    if not sector_scores:
        return {}
    sector_scores = sorted(sector_scores, key=lambda x: abs(x[1]), reverse=True)[:MAX_ETFS]
    denom = sum(abs(s) for _, s in sector_scores)
    if denom <= 0:
        return {}
    return {etf: float(GROSS_TARGET * score / denom) for etf, score in sector_scores}


def generate_signals(context: Any) -> dict[str, float]:
    return _weights_from_history(context.prices, getattr(context, "as_of", None))
