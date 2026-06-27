"""AR-121 ETF family-relative OHLCV liquidity-pressure proxy allocator.

Research verdict: rejected after real Alpaca/qfa daily OHLCV random-window testing.
This model is retained as a durable, timestamp-safe implementation artifact only;
it should not be promoted without fresh evidence.
"""
from __future__ import annotations

import pandas as pd

FAMILY = {
    "SPY": "broad_index", "QQQ": "broad_index", "IWM": "broad_index", "IVV": "broad_index",
    "XLF": "sector", "XLE": "sector", "XLV": "sector", "XLK": "sector",
    "SMH": "industry", "GDX": "industry", "XBI": "industry", "KRE": "industry",
    "TLT": "bond_duration", "IEF": "bond_duration", "BIL": "bond_duration", "SHY": "bond_duration",
    "HYG": "credit", "LQD": "credit", "AGG": "credit", "JNK": "credit",
    "GLD": "commodity", "SLV": "commodity", "USO": "commodity", "UNG": "commodity",
    "EEM": "international", "EFA": "international", "FXI": "international", "EWZ": "international",
    "IWF": "factor_style", "IJR": "factor_style", "IWD": "factor_style", "VTV": "factor_style",
    "IYR": "real_assets", "VNQ": "real_assets", "XME": "real_assets", "URA": "real_assets",
}


def _zscore(frame: pd.DataFrame, window: int) -> pd.DataFrame:
    min_periods = max(10, window // 2)
    mean = frame.rolling(window, min_periods=min_periods).mean()
    std = frame.rolling(window, min_periods=min_periods).std().replace(0.0, pd.NA)
    return (frame - mean) / std


def _family_neutral(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy() * pd.NA
    for fam in sorted(set(FAMILY.values())):
        cols = [c for c in frame.columns if FAMILY.get(c) == fam]
        if not cols:
            continue
        sub = frame[cols]
        median = sub.median(axis=1)
        scale = sub.sub(median, axis=0).std(axis=1).replace(0.0, pd.NA)
        out[cols] = sub.sub(median, axis=0).div(scale, axis=0)
    return out.clip(-5.0, 5.0).fillna(0.0)


def generate_signals(context) -> dict[str, float]:
    """Return long-only weights for ETFs with negative family-relative liquidity pressure.

    Expects context.prices columns: timestamp, symbol, open, high, low, close, volume.
    Signals are computed only from data at or before context.as_of.
    """
    symbols = [s for s in context.symbols if s in FAMILY]
    if not symbols:
        return {}
    prices = context.prices.copy()
    prices["timestamp"] = pd.to_datetime(prices["timestamp"], utc=True)
    prices = prices[prices["symbol"].isin(symbols)].sort_values(["timestamp", "symbol"])
    if prices.empty:
        return {}

    close = prices.pivot(index="timestamp", columns="symbol", values="close").ffill()
    openp = prices.pivot(index="timestamp", columns="symbol", values="open").reindex_like(close).ffill()
    high = prices.pivot(index="timestamp", columns="symbol", values="high").reindex_like(close).ffill()
    low = prices.pivot(index="timestamp", columns="symbol", values="low").reindex_like(close).ffill()
    volume = prices.pivot(index="timestamp", columns="symbol", values="volume").reindex_like(close).fillna(0.0)
    if len(close) < 80:
        return {}

    ret1 = close.pct_change()
    dollar_volume = close * volume
    # log1p without importing numpy: pandas supports elementwise apply here and history is small at live use.
    log_dv = dollar_volume.map(lambda x: 0.0 if pd.isna(x) or x <= 0 else __import__("math").log1p(float(x)))
    volshock = _zscore(log_dv, 60).clip(-5.0, 5.0).fillna(0.0)
    clv = ((close - low) / (high - low).replace(0.0, pd.NA) * 2.0 - 1.0).clip(-1.0, 1.0).fillna(0.0)
    gap = (openp / close.shift(1) - 1.0).replace([float("inf"), -float("inf")], pd.NA).fillna(0.0)
    intraday = (close / openp - 1.0).replace([float("inf"), -float("inf")], pd.NA).fillna(0.0)
    range_frame = (high / low).replace([float("inf"), -float("inf")], pd.NA)
    log_range = range_frame.map(lambda x: 0.0 if pd.isna(x) or x <= 0 else __import__("math").log(float(x)))

    signed_vol_pressure = volshock * ret1.fillna(0.0).map(lambda x: 1.0 if x > 0 else (-1.0 if x < 0 else 0.0))
    pressure = (
        0.35 * _family_neutral(_zscore(ret1, 20))
        + 0.25 * _family_neutral(signed_vol_pressure)
        + 0.20 * _family_neutral(clv)
        + 0.10 * _family_neutral(_zscore(gap + intraday, 60))
        + 0.10 * _family_neutral(_zscore(log_range, 60))
    )
    score = (-pressure.iloc[-1]).dropna()
    picks = score[score > 0.85].sort_values(ascending=False).head(8)
    if picks.empty:
        return {s: 0.0 for s in symbols}

    invvol = 1.0 / ret1.rolling(60, min_periods=20).std().iloc[-1][picks.index].replace(0.0, pd.NA)
    invvol = invvol.replace([float("inf"), -float("inf")], pd.NA).fillna(1.0)
    weights = (invvol / invvol.sum()).clip(upper=0.25)
    weights = weights / weights.sum()
    return {s: float(weights.get(s, 0.0)) for s in symbols}
