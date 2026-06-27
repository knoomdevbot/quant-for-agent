"""AR-076 mega-cap volatility contraction breakout continuation.

QFA contract: expose generate_signals(context) -> dict[str, float].
Research-only model; uses only OHLCV bars supplied by qfa/Alpaca and never
places orders.

Mechanism: mega-cap stocks that exit a low realized range/volatility regime on
abnormal volume with idiosyncratic breakout strength are followed for several
sessions. This is deliberately divergent from AR-068's residual close-location
reversal: positive residual breakout -> long continuation; negative breakdown ->
short continuation.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

UNIVERSE = ("AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "AVGO", "TSLA", "JPM", "LLY")


class ModelParams:
    contraction_window = 15
    contraction_rank_window = 90
    breakout_lookback = 20
    volume_z_window = 60
    residual_z_window = 60
    volatility_window = 20
    basket_vol_window = 20
    basket_vol_rank_window = 252
    min_history = 120
    max_history_need = 280
    max_abs_weight = 0.22
    min_symbols = 6
    contraction_percentile = 0.35
    min_breakout_pct = 0.0025
    volume_z_entry = 0.75
    residual_z_entry = 0.45
    high_market_vol_brake = 0.65
    high_market_vol_rank = 0.80
    hold_decay = (1.00, 0.75, 0.50, 0.30)


PARAMS = ModelParams()


def _zero(symbols: list[str]) -> dict[str, float]:
    return {s: 0.0 for s in symbols}


def _wide(prices: pd.DataFrame, symbols: list[str]) -> dict[str, pd.DataFrame] | None:
    if prices is None or prices.empty:
        return None
    p = prices[prices["symbol"].isin(symbols)].copy()
    if p.empty:
        return None
    p["timestamp"] = pd.to_datetime(p["timestamp"], utc=True)
    wide = {}
    for col in ("open", "high", "low", "close", "volume"):
        if col not in p.columns:
            return None
        wide[col] = p.pivot(index="timestamp", columns="symbol", values=col).sort_index().ffill()
    return wide


def _zscore(x: pd.DataFrame, window: int) -> pd.DataFrame:
    mean = x.shift(1).rolling(window, min_periods=window).mean()
    std = x.shift(1).rolling(window, min_periods=window).std(ddof=1)
    return ((x - mean) / std).replace([np.inf, -np.inf], np.nan)


def _normalize(scores: dict[str, float], symbols: list[str]) -> dict[str, float]:
    vals = pd.Series({s: float(scores.get(s, 0.0)) for s in symbols}, dtype=float).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    if vals.abs().sum() <= 0:
        return _zero(symbols)
    # Dollar-neutral cross section, then cap individual names and gross-normalize.
    vals = vals - vals.mean()
    vals = vals.where(vals.abs() >= 1e-12, 0.0)
    if vals.abs().sum() <= 0:
        return _zero(symbols)
    vals = vals / vals.abs().sum()
    vals = vals.clip(lower=-PARAMS.max_abs_weight, upper=PARAMS.max_abs_weight)
    gross = float(vals.abs().sum())
    if gross <= 0:
        return _zero(symbols)
    vals = vals / gross
    return {s: float(vals.get(s, 0.0)) for s in symbols}


def generate_signals(context) -> dict[str, float]:
    """Return next-bar target weights for volatility-contraction breakouts."""
    output_symbols = list(getattr(context, "symbols", []) or [])
    symbols = [s for s in output_symbols if s in UNIVERSE]
    if len(symbols) < PARAMS.min_symbols:
        return _zero(output_symbols)
    wide = _wide(getattr(context, "prices", pd.DataFrame()), symbols)
    if wide is None:
        return _zero(output_symbols)

    close = wide["close"][symbols].dropna(axis=1, how="any")
    tradable = [s for s in symbols if s in close.columns]
    if len(tradable) < PARAMS.min_symbols or len(close) < PARAMS.min_history:
        return _zero(output_symbols)
    high = wide["high"][tradable]
    low = wide["low"][tradable]
    volume = wide["volume"][tradable]
    close = wide["close"][tradable]

    p = PARAMS
    ret = close.pct_change().replace([np.inf, -np.inf], np.nan)
    basket_ret = ret.mean(axis=1)
    residual_ret = ret.sub(basket_ret, axis=0)
    residual_z = _zscore(residual_ret, p.residual_z_window)

    # Completed-bar realized range contraction: recent high-low range relative to price.
    range_width = (high.rolling(p.contraction_window, min_periods=p.contraction_window).max() /
                   low.rolling(p.contraction_window, min_periods=p.contraction_window).min() - 1.0)
    contraction_rank = range_width.rolling(p.contraction_rank_window, min_periods=30).rank(pct=True)

    prior_high = high.shift(1).rolling(p.breakout_lookback, min_periods=p.breakout_lookback).max()
    prior_low = low.shift(1).rolling(p.breakout_lookback, min_periods=p.breakout_lookback).min()
    up_break = (close / prior_high - 1.0).replace([np.inf, -np.inf], np.nan)
    dn_break = (close / prior_low - 1.0).replace([np.inf, -np.inf], np.nan)

    log_vol = np.log(volume.where(volume > 0))
    volume_z = _zscore(log_vol, p.volume_z_window)

    vol = ret.shift(1).rolling(p.volatility_window, min_periods=p.volatility_window).std(ddof=1)
    inv_vol = (1.0 / vol).replace([np.inf, -np.inf], np.nan)
    inv_vol = inv_vol.div(inv_vol.median(axis=1), axis=0).clip(lower=0.50, upper=1.75).fillna(1.0)

    basket_vol = basket_ret.rolling(p.basket_vol_window, min_periods=p.basket_vol_window).std(ddof=1)
    basket_vol_rank = basket_vol.rolling(p.basket_vol_rank_window, min_periods=60).rank(pct=True)
    latest = close.index[-1]
    brake = p.high_market_vol_brake if (latest in basket_vol_rank.index and pd.notna(basket_vol_rank.loc[latest]) and float(basket_vol_rank.loc[latest]) > p.high_market_vol_rank) else 1.0

    raw = {s: 0.0 for s in output_symbols}
    for age, decay in enumerate(p.hold_decay):
        idx = -1 - age
        if len(close) < abs(idx):
            continue
        ts = close.index[idx]
        for s in tradable:
            cr = contraction_rank.loc[ts, s] if ts in contraction_rank.index else np.nan
            vz = volume_z.loc[ts, s] if ts in volume_z.index else np.nan
            rz = residual_z.loc[ts, s] if ts in residual_z.index else np.nan
            ub = up_break.loc[ts, s] if ts in up_break.index else np.nan
            db = dn_break.loc[ts, s] if ts in dn_break.index else np.nan
            if pd.isna(cr) or pd.isna(vz) or pd.isna(rz):
                continue
            if float(cr) > p.contraction_percentile or float(vz) < p.volume_z_entry:
                continue
            direction = 0
            breakout_strength = 0.0
            if pd.notna(ub) and float(ub) >= p.min_breakout_pct and float(rz) >= p.residual_z_entry:
                direction = 1
                breakout_strength = float(ub) / p.min_breakout_pct + max(float(rz) - p.residual_z_entry, 0.0)
            elif pd.notna(db) and float(db) <= -p.min_breakout_pct and float(rz) <= -p.residual_z_entry:
                direction = -1
                breakout_strength = abs(float(db)) / p.min_breakout_pct + max(abs(float(rz)) - p.residual_z_entry, 0.0)
            if direction == 0:
                continue
            vol_scale = float(inv_vol.loc[ts, s]) if ts in inv_vol.index and pd.notna(inv_vol.loc[ts, s]) else 1.0
            contraction_bonus = max(0.0, p.contraction_percentile - float(cr)) / max(p.contraction_percentile, 1e-9)
            volume_bonus = 1.0 + 0.12 * min(max(float(vz) - p.volume_z_entry, 0.0), 4.0)
            raw[s] += direction * decay * breakout_strength * (1.0 + contraction_bonus) * volume_bonus * vol_scale * brake

    return _normalize(raw, output_symbols)
