"""AR-068 residual close-location reversal, opportunity-balanced v1.

QFA contract: expose generate_signals(context) -> dict[str, float].
Uses only OHLCV bars already present in qfa/Alpaca context; no external data.

Signal intuition: identify idiosyncratic one-day exhaustion versus an equal-weight
mega-cap basket. Prefer long positions in lower-tail residual losers closing near
their lows on abnormal volume, and shorts in upper-tail residual winners closing
near their highs. Scores are ranked instead of hard z-gated to keep opportunity
count higher than sparse residual-threshold variants.
"""
from __future__ import annotations

import math
from typing import Dict

import numpy as np
import pandas as pd

UNIVERSE = ["AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "AVGO", "TSLA", "JPM", "LLY"]
LOOKBACK = 60
BETA_LOOKBACK = 60
VOL_LOOKBACK = 20
MIN_HISTORY = 65
RESIDUAL_RANK_Q = 0.72
VOLUME_Z_MIN = 1.25
CLOSE_LOCATION_EDGE = 0.84
MAX_ABS_NAME_RAW = 0.28
SOFT_REGIME_LOOKBACK = 20


def _pivot(prices: pd.DataFrame, field: str) -> pd.DataFrame:
    return (
        prices.pivot(index="timestamp", columns="symbol", values=field)
        .sort_index()
        .ffill()
    )


def _safe_z(x: pd.Series) -> pd.Series:
    std = x.std(ddof=0)
    if not np.isfinite(std) or std <= 1e-12:
        return pd.Series(0.0, index=x.index)
    return (x - x.mean()) / std


def generate_signals(context) -> Dict[str, float]:
    symbols = [s for s in context.symbols if s in UNIVERSE]
    if len(symbols) < 4:
        return {s: 0.0 for s in context.symbols}

    px = context.prices.copy()
    if px.empty:
        return {s: 0.0 for s in context.symbols}
    px["timestamp"] = pd.to_datetime(px["timestamp"], utc=True)
    px = px[px["symbol"].isin(symbols)].sort_values(["timestamp", "symbol"])

    close = _pivot(px, "close").reindex(columns=symbols)
    high = _pivot(px, "high").reindex(columns=symbols)
    low = _pivot(px, "low").reindex(columns=symbols)
    volume = _pivot(px, "volume").reindex(columns=symbols)
    if len(close) < MIN_HISTORY:
        return {s: 0.0 for s in context.symbols}

    close = close.tail(max(LOOKBACK + 5, BETA_LOOKBACK + 5, MIN_HISTORY))
    high = high.reindex(close.index).ffill()
    low = low.reindex(close.index).ffill()
    volume = volume.reindex(close.index).ffill()

    rets = close.pct_change().dropna(how="all")
    if len(rets) < BETA_LOOKBACK:
        return {s: 0.0 for s in context.symbols}

    basket_ret = rets[symbols].mean(axis=1)
    beta_window = rets.tail(BETA_LOOKBACK)
    mkt_window = basket_ret.reindex(beta_window.index)
    var_m = float(mkt_window.var(ddof=0))
    beta = {}
    for s in symbols:
        cov = float(beta_window[s].cov(mkt_window)) if s in beta_window else 0.0
        beta[s] = cov / var_m if var_m > 1e-12 and np.isfinite(cov) else 1.0

    today_ret = rets.iloc[-1].reindex(symbols).fillna(0.0)
    today_basket = float(today_ret.mean())
    residual = pd.Series({s: float(today_ret[s] - beta[s] * today_basket) for s in symbols})
    resid_pct = residual.rank(pct=True)

    rng = (high.iloc[-1] - low.iloc[-1]).replace(0.0, np.nan)
    close_loc = ((close.iloc[-1] - low.iloc[-1]) / rng).reindex(symbols).fillna(0.5).clip(0.0, 1.0)

    dollar_vol = (volume * close).replace([np.inf, -np.inf], np.nan)
    vol_z = pd.Series(index=symbols, dtype=float)
    for s in symbols:
        hist = dollar_vol[s].tail(21).dropna()
        if len(hist) < 10:
            vol_z[s] = 0.0
        else:
            vol_z[s] = float(_safe_z(np.log(hist + 1.0)).iloc[-1])
    vol_boost = ((vol_z - VOLUME_Z_MIN) / 1.5).clip(lower=0.0, upper=1.0)

    vol = rets[symbols].tail(VOL_LOOKBACK).std(ddof=0).replace(0.0, np.nan)
    inv_vol = (1.0 / vol).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    inv_vol = inv_vol / inv_vol.mean() if inv_vol.mean() > 0 else pd.Series(1.0, index=symbols)

    raw = pd.Series(0.0, index=symbols)
    for s in symbols:
        # Long idiosyncratic loser closing near low; short idiosyncratic winner closing near high.
        long_tail = max(0.0, (RESIDUAL_RANK_Q - float(resid_pct[s])) / RESIDUAL_RANK_Q)
        short_tail = max(0.0, (float(resid_pct[s]) - (1.0 - RESIDUAL_RANK_Q)) / RESIDUAL_RANK_Q)
        low_close = max(0.0, (CLOSE_LOCATION_EDGE - float(close_loc[s])) / CLOSE_LOCATION_EDGE)
        high_close = max(0.0, (float(close_loc[s]) - (1.0 - CLOSE_LOCATION_EDGE)) / CLOSE_LOCATION_EDGE)
        liq = 0.55 + 0.45 * float(vol_boost[s])
        raw[s] = (long_tail * low_close - short_tail * high_close) * liq * float(inv_vol[s])

    # Soft regime gate: reduce but do not eliminate exposure in high-drift market regimes.
    recent_mkt = basket_ret.tail(SOFT_REGIME_LOOKBACK)
    regime_z = 0.0 if recent_mkt.std(ddof=0) <= 1e-12 else float(recent_mkt.mean() / recent_mkt.std(ddof=0) * math.sqrt(252))
    gate = 1.0 / (1.0 + 0.20 * abs(regime_z))
    raw *= max(0.35, min(1.0, gate))

    # Cross-sectional dollar-neutral and approximate beta-neutral projection.
    if raw.abs().sum() <= 1e-12:
        return {s: 0.0 for s in context.symbols}
    raw -= raw.mean()
    beta_vec = pd.Series(beta).reindex(symbols).fillna(1.0)
    denom = float((beta_vec * beta_vec).sum())
    if denom > 1e-12:
        raw -= beta_vec * float((raw * beta_vec).sum()) / denom

    raw = raw.clip(lower=-MAX_ABS_NAME_RAW, upper=MAX_ABS_NAME_RAW)
    gross = float(raw.abs().sum())
    if gross <= 1e-12:
        return {s: 0.0 for s in context.symbols}
    raw /= gross
    return {s: float(raw.get(s, 0.0)) for s in context.symbols}
