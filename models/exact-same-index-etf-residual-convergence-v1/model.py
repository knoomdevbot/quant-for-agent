"""AR-133 exact same-index ETF residual convergence model.

QFA contract: expose generate_signals(context) -> dict[symbol, weight].
Uses only completed daily OHLCV closes supplied by qfa/Alpaca.  The universe is
restricted ex ante to exact/near-identical benchmark ETF substitute clusters.
No daemon, no orders, no CSV inputs.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

CLUSTERS = {
    "sp500_exact_substitutes": ["SPY", "IVV", "VOO", "SPLG"],
    "nasdaq100_exact_substitutes": ["QQQ", "QQQM"],
    "russell2000_near_substitutes": ["IWM", "VTWO"],
    "total_us_market_near_substitutes": ["VTI", "ITOT", "SCHB"],
    "aggregate_bond_near_substitutes": ["AGG", "BND"],
}
UNIVERSE = sorted({s for members in CLUSTERS.values() for s in members})
PARAMS = {
    "lookback": 126,
    "min_history": 140,
    "entry_z": 2.0,
    "exit_z": 0.35,
    "amplitude_floor_log": 0.0010,
    "max_gross": 1.0,
    "cluster_cap": 0.24,
    "symbol_cap": 0.12,
}


def _zero(symbols: list[str]) -> dict[str, float]:
    return {s: 0.0 for s in symbols}


def _close_matrix(context) -> pd.DataFrame:
    prices = getattr(context, "prices", None)
    symbols = list(getattr(context, "symbols", []) or [])
    if prices is None or prices.empty or not {"timestamp", "symbol", "close"}.issubset(prices.columns):
        return pd.DataFrame()
    allowed = [s for s in UNIVERSE if s in symbols]
    if not allowed:
        return pd.DataFrame()
    p = prices[prices["symbol"].isin(allowed)].copy()
    p["timestamp"] = pd.to_datetime(p["timestamp"], utc=True)
    return p.pivot(index="timestamp", columns="symbol", values="close").sort_index().ffill()


def generate_signals(context) -> dict[str, float]:
    """Return next-bar target weights from lagged same-index residual z-scores."""
    symbols = list(getattr(context, "symbols", []) or [])
    if not symbols:
        return {}
    close = _close_matrix(context)
    if close.empty or len(close) < PARAMS["min_history"]:
        return _zero(symbols)

    logp = close.where(close > 0).apply(np.log)
    raw = {s: 0.0 for s in symbols}
    p = PARAMS
    active_clusters = 0

    for cname, members0 in CLUSTERS.items():
        members = [s for s in members0 if s in logp.columns and s in symbols]
        block = logp[members].dropna()
        if len(members) < 2 or len(block) < p["min_history"]:
            continue
        resid = block.sub(block.mean(axis=1), axis=0)
        rmean = resid.rolling(p["lookback"]).mean()
        rstd = resid.rolling(p["lookback"]).std(ddof=1)
        z = ((resid - rmean) / rstd).iloc[-1].dropna()
        amp = (resid - rmean).iloc[-1].abs().dropna()
        tradable = [s for s in z.index if abs(float(z[s])) >= p["entry_z"] and float(amp.get(s, 0.0)) >= p["amplitude_floor_log"]]
        if len(tradable) < 2:
            # For pairs, a single extreme implies the opposite leg in the same cluster.
            if len(members) == 2 and len(z) == 2 and z.abs().max() >= p["entry_z"] and amp.max() >= p["amplitude_floor_log"]:
                tradable = list(z.index)
            else:
                continue
        scores = {s: -float(z[s]) for s in tradable}
        # Enforce cluster dollar-neutrality: long cheap/negative residual, short rich/positive residual.
        ser = pd.Series(scores, dtype=float)
        ser = ser - ser.mean()
        gross = float(ser.abs().sum())
        if gross <= 0:
            continue
        active_clusters += 1
        scale = min(p["cluster_cap"], p["max_gross"]) / gross
        for s, v in ser.items():
            raw[s] += float(v) * scale

    if active_clusters == 0:
        return _zero(symbols)
    capped = {s: max(-p["symbol_cap"], min(p["symbol_cap"], raw.get(s, 0.0))) for s in symbols}
    gross = sum(abs(v) for v in capped.values())
    if gross <= 0:
        return _zero(symbols)
    scale = min(1.0, p["max_gross"] / gross)
    return {s: float(capped[s] * scale) for s in symbols}
