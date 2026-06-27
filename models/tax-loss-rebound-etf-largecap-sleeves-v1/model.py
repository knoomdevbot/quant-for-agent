
"""AR-123 timestamp-safe tax-loss rebound basket.

The qfa model is intentionally deterministic and dependency-light. It uses only
AlphaContext.prices daily OHLCV. On late-December rebalance dates it ranks a
fixed ETF sleeve and fixed large-cap equity sleeve by year-to-date total return
as of the last observed close on or before Dec. 20, then buys the worst prior
YTD losers for a short early-January rebound basket. On non-event days it
returns cash/zero weights.
"""
from __future__ import annotations

ETF_SYMBOLS = [
    'SPY','IVV','VOO','QQQ','IWM','DIA','MDY','RSP','VTI','VEA','EFA','EEM','IEMG','EWJ','EWG','EWU','EWC','FXI','INDA','EWZ',
    'XLK','XLF','XLE','XLV','XLY','XLP','XLI','XLB','XLU','XLRE','XLC','SMH','IYT','ITB','XBI','KRE','KBE','XRT','GDX','SLV','GLD','USO',
    'TLT','IEF','SHY','LQD','HYG','JNK','TIP','BND','AGG','VNQ','IYR','DBC','PDBC','MTUM','QUAL','USMV','VLUE','SPLV'
]
EQUITY_SYMBOLS = [
    'AAPL','MSFT','NVDA','AMZN','META','GOOGL','GOOG','BRK.B','LLY','AVGO','JPM','V','XOM','UNH','MA','PG','COST','HD','JNJ','ABBV',
    'BAC','KO','NFLX','CRM','AMD','PEP','TMO','WMT','ADBE','CSCO','MCD','ABT','ACN','LIN','ORCL','INTC','DIS','VZ','CMCSA','NKE',
    'TXN','QCOM','PM','NEE','UPS','LOW','HON','RTX','IBM','CAT','GE','GS','MS','BLK','AXP','SPGI','NOW','AMAT','ISRG','BKNG',
    'AMGN','GILD','PFE','MRK','CVX','COP','SLB','BA','DE','LMT','MDT','SYK','TJX','ADP','INTU','AMT','PLD','T','MO','C','USB'
]
ETF_COUNT = 5
EQUITY_COUNT = 10
ETF_SLEEVE_WEIGHT = 0.50
EQUITY_SLEEVE_WEIGHT = 0.50
SIGNAL_MONTH = 12
SIGNAL_DAY_CUTOFF = 20
REBALANCE_DAY_MIN = 28


def _rank_losers(prices, symbols, year, count):
    year_prices = prices[(prices['timestamp'].dt.year == year) & (prices['symbol'].isin(symbols))]
    if year_prices.empty:
        return []
    signal_prices = year_prices[year_prices['timestamp'].dt.month.lt(12) | ((year_prices['timestamp'].dt.month == 12) & (year_prices['timestamp'].dt.day <= SIGNAL_DAY_CUTOFF))]
    if signal_prices.empty:
        return []
    pivot = signal_prices.pivot_table(index='timestamp', columns='symbol', values='close', aggfunc='last').sort_index().ffill()
    if pivot.empty:
        return []
    first = pivot.apply(lambda col: col.dropna().iloc[0] if col.notna().any() else None)
    last = pivot.apply(lambda col: col.dropna().iloc[-1] if col.notna().any() else None)
    returns = ((last / first) - 1.0).dropna().sort_values()
    return list(returns.head(count).index)


def generate_signals(context):
    import pandas as pd

    as_of = pd.Timestamp(context.as_of)
    if as_of.month != SIGNAL_MONTH or as_of.day < REBALANCE_DAY_MIN:
        return {}
    prices = context.prices.copy()
    if prices.empty:
        return {}
    prices['timestamp'] = pd.to_datetime(prices['timestamp'], utc=True)
    prices = prices[prices['timestamp'] <= as_of]
    available = set(context.symbols)
    etf_symbols = [s for s in ETF_SYMBOLS if s in available]
    equity_symbols = [s for s in EQUITY_SYMBOLS if s in available]
    etf_losers = _rank_losers(prices, etf_symbols, as_of.year, ETF_COUNT)
    equity_losers = _rank_losers(prices, equity_symbols, as_of.year, EQUITY_COUNT)
    weights = {}
    if etf_losers:
        for symbol in etf_losers:
            weights[symbol] = ETF_SLEEVE_WEIGHT / len(etf_losers)
    if equity_losers:
        for symbol in equity_losers:
            weights[symbol] = weights.get(symbol, 0.0) + EQUITY_SLEEVE_WEIGHT / len(equity_losers)
    return weights
