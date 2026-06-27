"""AR-130 SEC 13F deadline mega-cap attention residual-pressure reversal.

Rule-based qfa model. Uses only completed daily OHLCV in context.prices and a
public deterministic 13F deadline calendar (45 calendar days after quarter-end,
shifted to next observed trading day). After a completed deadline session, hold
for three sessions: long negative pre-deadline residual pressure and short
positive pressure among liquid mapped large caps with abnormal dollar volume.
No CSV, daemon, or orders are used by this model.
"""
from __future__ import annotations
from typing import Any
import numpy as np
import pandas as pd

SECTOR = {'AAPL': 'XLK',
 'ABBV': 'XLV',
 'ABT': 'XLV',
 'ADBE': 'XLK',
 'ADI': 'XLK',
 'ADP': 'XLI',
 'AEP': 'XLU',
 'AMAT': 'XLK',
 'AMD': 'XLK',
 'AMGN': 'XLV',
 'AMT': 'XLRE',
 'AMZN': 'XLY',
 'ANET': 'XLK',
 'AON': 'XLF',
 'APD': 'XLB',
 'APH': 'XLK',
 'AVGO': 'XLK',
 'AXP': 'XLF',
 'BA': 'XLI',
 'BAC': 'XLF',
 'BKNG': 'XLY',
 'BLK': 'XLF',
 'BMY': 'XLV',
 'BSX': 'XLV',
 'C': 'XLF',
 'CAT': 'XLI',
 'CB': 'XLF',
 'CDNS': 'XLK',
 'CHTR': 'XLC',
 'CI': 'XLV',
 'CL': 'XLP',
 'CMCSA': 'XLC',
 'CME': 'XLF',
 'CMG': 'XLY',
 'COF': 'XLF',
 'COP': 'XLE',
 'COST': 'XLP',
 'CRM': 'XLK',
 'CVX': 'XLE',
 'D': 'XLU',
 'DD': 'XLB',
 'DE': 'XLI',
 'DHR': 'XLV',
 'DIS': 'XLC',
 'DUK': 'XLU',
 'EA': 'XLC',
 'ECL': 'XLB',
 'ELV': 'XLV',
 'EMR': 'XLI',
 'EOG': 'XLE',
 'EQIX': 'XLRE',
 'ETN': 'XLI',
 'EXC': 'XLU',
 'FCX': 'XLB',
 'FTNT': 'XLK',
 'GD': 'XLI',
 'GE': 'XLI',
 'GILD': 'XLV',
 'GIS': 'XLP',
 'GOOG': 'XLC',
 'GOOGL': 'XLC',
 'GS': 'XLF',
 'HD': 'XLY',
 'HLT': 'XLY',
 'HON': 'XLI',
 'IBM': 'XLK',
 'ICE': 'XLF',
 'INTC': 'XLK',
 'INTU': 'XLK',
 'ISRG': 'XLV',
 'ITW': 'XLI',
 'JNJ': 'XLV',
 'JPM': 'XLF',
 'KLAC': 'XLK',
 'KMB': 'XLP',
 'KO': 'XLP',
 'LIN': 'XLB',
 'LLY': 'XLV',
 'LMT': 'XLI',
 'LOW': 'XLY',
 'LRCX': 'XLK',
 'MA': 'XLF',
 'MAR': 'XLY',
 'MCD': 'XLY',
 'MDLZ': 'XLP',
 'MDT': 'XLV',
 'META': 'XLC',
 'MMC': 'XLF',
 'MMM': 'XLI',
 'MO': 'XLP',
 'MPC': 'XLE',
 'MRK': 'XLV',
 'MS': 'XLF',
 'MSFT': 'XLK',
 'MSI': 'XLK',
 'MU': 'XLK',
 'NEE': 'XLU',
 'NEM': 'XLB',
 'NFLX': 'XLC',
 'NKE': 'XLY',
 'NOC': 'XLI',
 'NOW': 'XLK',
 'NVDA': 'XLK',
 'ORCL': 'XLK',
 'ORLY': 'XLY',
 'OXY': 'XLE',
 'PANW': 'XLK',
 'PEG': 'XLU',
 'PEP': 'XLP',
 'PFE': 'XLV',
 'PG': 'XLP',
 'PGR': 'XLF',
 'PLD': 'XLRE',
 'PM': 'XLP',
 'PNC': 'XLF',
 'PSX': 'XLE',
 'QCOM': 'XLK',
 'RCL': 'XLY',
 'REGN': 'XLV',
 'RTX': 'XLI',
 'SBUX': 'XLY',
 'SCHW': 'XLF',
 'SHOP': 'XLK',
 'SHW': 'XLB',
 'SLB': 'XLE',
 'SNPS': 'XLK',
 'SO': 'XLU',
 'SPG': 'XLRE',
 'SPGI': 'XLF',
 'SRE': 'XLU',
 'SYK': 'XLV',
 'T': 'XLC',
 'TGT': 'XLP',
 'TJX': 'XLY',
 'TMO': 'XLV',
 'TMUS': 'XLC',
 'TSLA': 'XLY',
 'TT': 'XLI',
 'TTWO': 'XLC',
 'TXN': 'XLK',
 'UNH': 'XLV',
 'UNP': 'XLI',
 'UPS': 'XLI',
 'USB': 'XLF',
 'V': 'XLF',
 'VLO': 'XLE',
 'VRTX': 'XLV',
 'VZ': 'XLC',
 'WELL': 'XLRE',
 'WFC': 'XLF',
 'WMT': 'XLP',
 'XOM': 'XLE'}
SELECTED = ['TSLA',
 'AAPL',
 'AMZN',
 'MSFT',
 'META',
 'NVDA',
 'AMD',
 'GOOGL',
 'GOOG',
 'BA',
 'NFLX',
 'V',
 'BAC',
 'JPM',
 'DIS',
 'INTC',
 'MA',
 'MU',
 'SHOP',
 'C',
 'XOM',
 'CRM',
 'UNH',
 'JNJ',
 'T',
 'WFC',
 'PFE',
 'HD',
 'ADBE',
 'PG',
 'QCOM',
 'CVX',
 'VZ',
 'WMT',
 'CMCSA',
 'MRK',
 'KO',
 'AVGO',
 'COST',
 'BMY',
 'BKNG',
 'ORCL',
 'ABBV',
 'NKE',
 'GE',
 'GS',
 'TXN',
 'MCD',
 'SBUX',
 'PEP',
 'MS',
 'AMGN',
 'IBM',
 'NOW',
 'LOW',
 'LRCX',
 'UNP',
 'TMO',
 'LLY',
 'CHTR',
 'CAT',
 'TGT',
 'AMAT',
 'MDT',
 'ABT',
 'NEE',
 'HON',
 'GILD',
 'DHR',
 'RTX',
 'UPS',
 'LMT',
 'MMM',
 'AXP',
 'AMT',
 'PM',
 'TMUS',
 'COP',
 'INTU',
 'OXY',
 'ELV',
 'ISRG',
 'LIN',
 'SCHW',
 'MO',
 'SPGI',
 'REGN',
 'CI',
 'TJX',
 'CMG',
 'MDLZ',
 'NEM',
 'BLK',
 'DE',
 'ADI',
 'SLB',
 'MPC',
 'VRTX',
 'EA',
 'ADP',
 'USB',
 'FCX',
 'SHW',
 'BSX',
 'SPG',
 'EOG',
 'DUK',
 'DD',
 'NOC',
 'EQIX',
 'RCL',
 'CME',
 'PANW',
 'CL',
 'PNC',
 'D',
 'VLO',
 'AON',
 'COF',
 'PLD',
 'MAR',
 'SYK',
 'KLAC',
 'APD',
 'CB',
 'SO',
 'ICE',
 'EXC',
 'PSX',
 'ORLY']
HOLD_DAYS = 3
PRE_WINDOW = 5
VOL_LOOKBACK = 120
TOP_FRACTION = 0.20
MIN_NAMES = 40
MAX_SECTOR_GROSS = 0.25


def _deadline_events(index: pd.DatetimeIndex) -> list[pd.Timestamp]:
    out = []
    if len(index) == 0:
        return out
    for year in range(int(index[0].year), int(index[-1].year) + 1):
        for month, day in [(3, 31), (6, 30), (9, 30), (12, 31)]:
            raw = pd.Timestamp(year, month, day) + pd.Timedelta(days=45)
            candidates = index[index >= raw]
            if len(candidates):
                out.append(pd.Timestamp(candidates[0]))
    return sorted(set(out))


def _active_deadline(as_of: pd.Timestamp, index: pd.DatetimeIndex) -> pd.Timestamp | None:
    events = _deadline_events(index)
    if as_of not in index:
        return None
    loc = index.get_loc(as_of)
    for event in events:
        if event not in index:
            continue
        dist = loc - index.get_loc(event)
        if 0 <= dist < HOLD_DAYS:
            return event
    return None


def _sector_cap(weights: pd.Series) -> dict[str, float]:
    capped = weights.copy()
    for sector in sorted(set(SECTOR.values())):
        members = [s for s in capped.index if SECTOR.get(s) == sector]
        gross = float(capped.loc[members].abs().sum()) if members else 0.0
        if gross > MAX_SECTOR_GROSS:
            capped.loc[members] *= MAX_SECTOR_GROSS / gross
    gross = float(capped.abs().sum())
    if gross <= 0 or not np.isfinite(gross):
        return {}
    return {str(s): float(w / gross) for s, w in capped.items() if abs(float(w)) > 1e-12}


def generate_signals(context: Any) -> dict[str, float]:
    frame = context.prices.copy()
    if frame.empty:
        return {}
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True).dt.tz_convert(None).dt.normalize()
    close = frame.pivot_table(index="timestamp", columns="symbol", values="close", aggfunc="last").sort_index().ffill(limit=3)
    volume = frame.pivot_table(index="timestamp", columns="symbol", values="volume", aggfunc="last").sort_index().ffill(limit=1)
    symbols = [s for s in SELECTED if s in getattr(context, "symbols", []) and s in close.columns and SECTOR.get(s) in close.columns and "SPY" in close.columns]
    if len(symbols) < MIN_NAMES or len(close) < VOL_LOOKBACK + PRE_WINDOW + 5:
        return {}
    as_of = pd.Timestamp(getattr(context, "as_of", close.index[-1])).tz_localize(None).normalize()
    if as_of not in close.index:
        as_of = close.index[-1]
    event = _active_deadline(as_of, close.index)
    if event is None:
        return {}
    stock_ret = close[symbols].pct_change(PRE_WINDOW).loc[event]
    spy_ret = close["SPY"].pct_change(PRE_WINDOW).loc[event]
    residual = pd.Series(index=symbols, dtype=float)
    for symbol in symbols:
        residual.loc[symbol] = stock_ret.loc[symbol] - 0.6 * close[SECTOR[symbol]].pct_change(PRE_WINDOW).loc[event] - 0.4 * spy_ret
    dollar_volume = close[symbols] * volume[symbols]
    vol_z = ((dollar_volume.rolling(PRE_WINDOW).mean() - dollar_volume.rolling(VOL_LOOKBACK).mean()) / dollar_volume.rolling(VOL_LOOKBACK).std()).loc[event]
    score = residual[(vol_z > 0.0)].dropna()
    if len(score) < 20:
        return {}
    sleeve = max(8, int(len(score) * TOP_FRACTION))
    longs = score.nsmallest(sleeve).index
    shorts = score.nlargest(sleeve).index
    weights = pd.Series(0.0, index=symbols)
    weights.loc[longs] = 0.5 / len(longs)
    weights.loc[shorts] = -0.5 / len(shorts)
    return _sector_cap(weights)
