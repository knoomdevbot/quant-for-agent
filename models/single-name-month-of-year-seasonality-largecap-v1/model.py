"""AR-129 same-calendar-month large-cap seasonality model.

QFA contract: expose generate_signals(context) -> dict[str, float].  The rule uses
only completed daily OHLCV bars supplied in context.prices.  It derives monthly
close-to-close returns, then ranks stocks by the median return observed in the
same upcoming calendar month in prior years only.  No CSV input, daemon, orders,
or persistent raw market data are used by this module.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import numpy as np
import pandas as pd

SECTOR_ETF: dict[str, str] = {'AAPL': 'XLK', 'ABBV': 'XLV', 'ABT': 'XLV', 'ADBE': 'XLK', 'ADI': 'XLK', 'ADP': 'XLI', 'AEP': 'XLU', 'AMAT': 'XLK', 'AMD': 'XLK', 'AMGN': 'XLV', 'AMZN': 'XLY', 'ANET': 'XLK', 'AON': 'XLF', 'APD': 'XLB', 'APH': 'XLK', 'AVGO': 'XLK', 'AXP': 'XLF', 'BA': 'XLI', 'BAC': 'XLF', 'BKNG': 'XLY', 'BLK': 'XLF', 'BMY': 'XLV', 'BSX': 'XLV', 'C': 'XLF', 'CAT': 'XLI', 'CB': 'XLF', 'CDNS': 'XLK', 'CHTR': 'XLC', 'CI': 'XLV', 'CL': 'XLP', 'CMCSA': 'XLC', 'CME': 'XLF', 'CMG': 'XLY', 'COF': 'XLF', 'COP': 'XLE', 'COST': 'XLP', 'CRM': 'XLK', 'CVX': 'XLE', 'D': 'XLU', 'DD': 'XLB', 'DE': 'XLI', 'DHR': 'XLV', 'DIS': 'XLC', 'DUK': 'XLU', 'EA': 'XLC', 'ECL': 'XLB', 'ELV': 'XLV', 'EMR': 'XLI', 'EOG': 'XLE', 'ETN': 'XLI', 'EXC': 'XLU', 'FCX': 'XLB', 'FTNT': 'XLK', 'GD': 'XLI', 'GE': 'XLI', 'GILD': 'XLV', 'GIS': 'XLP', 'GOOG': 'XLC', 'GOOGL': 'XLC', 'GS': 'XLF', 'HD': 'XLY', 'HLT': 'XLY', 'HON': 'XLI', 'IBM': 'XLK', 'ICE': 'XLF', 'INTC': 'XLK', 'INTU': 'XLK', 'ISRG': 'XLV', 'ITW': 'XLI', 'JNJ': 'XLV', 'JPM': 'XLF', 'KLAC': 'XLK', 'KMB': 'XLP', 'KO': 'XLP', 'LLY': 'XLV', 'LMT': 'XLI', 'LOW': 'XLY', 'LRCX': 'XLK', 'MAR': 'XLY', 'MCD': 'XLY', 'MDLZ': 'XLP', 'MDT': 'XLV', 'META': 'XLC', 'MMC': 'XLF', 'MMM': 'XLI', 'MO': 'XLP', 'MPC': 'XLE', 'MRK': 'XLV', 'MS': 'XLF', 'MSFT': 'XLK', 'MSI': 'XLK', 'MU': 'XLK', 'NEE': 'XLU', 'NEM': 'XLB', 'NFLX': 'XLC', 'NKE': 'XLY', 'NOC': 'XLI', 'NOW': 'XLK', 'NVDA': 'XLK', 'ORCL': 'XLK', 'ORLY': 'XLY', 'OXY': 'XLE', 'PANW': 'XLK', 'PEG': 'XLU', 'PEP': 'XLP', 'PFE': 'XLV', 'PG': 'XLP', 'PGR': 'XLF', 'PM': 'XLP', 'PNC': 'XLF', 'PSX': 'XLE', 'QCOM': 'XLK', 'RCL': 'XLY', 'REGN': 'XLV', 'RTX': 'XLI', 'SBUX': 'XLY', 'SCHW': 'XLF', 'SHOP': 'XLK', 'SHW': 'XLB', 'SLB': 'XLE', 'SNPS': 'XLK', 'SO': 'XLU', 'SPGI': 'XLF', 'SRE': 'XLU', 'SYK': 'XLV', 'T': 'XLC', 'TGT': 'XLP', 'TJX': 'XLY', 'TMO': 'XLV', 'TMUS': 'XLC', 'TSLA': 'XLY', 'TTWO': 'XLC', 'TXN': 'XLK', 'UNH': 'XLV', 'UNP': 'XLI', 'UPS': 'XLI', 'USB': 'XLF', 'VLO': 'XLE', 'VRTX': 'XLV', 'VZ': 'XLC', 'WFC': 'XLF', 'WMT': 'XLP', 'XOM': 'XLE'}
MIN_MONTHS = 36
MIN_SAME_MONTH_OBS = 3
TOP_FRACTION = 0.20
MAX_SECTOR_GROSS = 0.25


def _monthly_returns(prices: pd.DataFrame) -> pd.DataFrame:
    frame = prices.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    close = frame.pivot_table(index="timestamp", columns="symbol", values="close", aggfunc="last").sort_index().ffill(limit=5)
    month_close = close.resample("ME").last()
    return month_close.pct_change().dropna(how="all")


def _next_month(ts: pd.Timestamp) -> int:
    return 1 if ts.month == 12 else ts.month + 1


def _sector_neutral_scores(scores: pd.Series) -> pd.Series:
    out = scores.copy()
    for sector in sorted(set(SECTOR_ETF.values())):
        members = [symbol for symbol, sec in SECTOR_ETF.items() if sec == sector and symbol in out.index]
        if members:
            out.loc[members] = out.loc[members] - out.loc[members].median()
    return out


def _cap_sector_gross(weights: pd.Series) -> dict[str, float]:
    gross_by_sector: dict[str, float] = defaultdict(float)
    for raw_symbol, weight in weights.items():
        symbol = str(raw_symbol)
        gross_by_sector[SECTOR_ETF[symbol]] += abs(float(weight))
    capped = weights.copy()
    for raw_symbol, weight in capped.items():
        symbol = str(raw_symbol)
        sector_gross = gross_by_sector[SECTOR_ETF[symbol]]
        if sector_gross > MAX_SECTOR_GROSS:
            capped.loc[symbol] = float(weight) * MAX_SECTOR_GROSS / sector_gross
    gross = float(capped.abs().sum())
    if gross <= 0 or not np.isfinite(gross):
        return {}
    return {str(symbol): float(weight / gross) for symbol, weight in capped.items() if abs(float(weight)) > 1e-12}


def generate_signals(context: Any) -> dict[str, float]:
    """Return monthly long/short target weights from lagged same-month seasonality."""
    symbols = [symbol for symbol in getattr(context, "symbols", []) if symbol in SECTOR_ETF]
    if len(symbols) < 40:
        return {}
    monthly = _monthly_returns(context.prices)
    available = [symbol for symbol in symbols if symbol in monthly.columns]
    if len(monthly) < MIN_MONTHS or len(available) < 40:
        return {}

    # The most recent completed month is in monthly.index[-1].  A live/research
    # rebalance for the next holding month can only use rows before that holding month.
    monthly.index = pd.DatetimeIndex(monthly.index)
    target_month = _next_month(pd.Timestamp(monthly.index[-1]))
    history = monthly[available]
    same_month = history[history.index.month == target_month]
    if len(same_month) < MIN_SAME_MONTH_OBS:
        return {}

    scores = _sector_neutral_scores(same_month.median().dropna())
    if len(scores) < 40:
        return {}
    sleeve = max(10, int(len(scores) * TOP_FRACTION))
    longs = scores.nlargest(sleeve).index
    shorts = scores.nsmallest(sleeve).index
    weights = pd.Series(0.0, index=scores.index)
    weights.loc[longs] = 0.5 / len(longs)
    weights.loc[shorts] = -0.5 / len(shorts)
    return _cap_sector_gross(weights)
