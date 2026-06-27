"""Post-gap residual continuation basket for mega-cap equities (AR-069).

QFA contract: expose generate_signals(context) -> dict[str, float].
Research-only model; it never places orders.

Mechanism: daily open/previous-close gaps are decomposed into a cross-sectional
(equal-weight basket) component and an idiosyncratic residual component. Large
residual gaps with abnormal volume are followed for several sessions with a
3-5 day decay, on the hypothesis that idiosyncratic information diffuses after
the initial overnight repricing. This is deliberately directionally opposite to
close-location/liquidity-exhaustion reversal families: positive residual gap ->
long, negative residual gap -> short.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

UNIVERSE = ("AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "AVGO", "TSLA", "JPM", "LLY")


class ModelParams:
    gap_z_window = 60
    volume_z_window = 60
    volatility_window = 20
    entry_residual_gap_z = 1.15
    min_abs_residual_gap = 0.003
    abnormal_volume_z = 0.20
    hold_decay = (1.00, 0.75, 0.55, 0.35, 0.20)
    max_abs_weight = 0.24
    min_symbols = 5
    high_market_vol_brake = 0.82
    market_vol_window = 20
    market_vol_high_quantile_window = 252


PARAMS = ModelParams()


def _zero(symbols):
    return {symbol: 0.0 for symbol in symbols}


def _wide(prices: pd.DataFrame, symbols: list[str]):
    px = prices[prices["symbol"].isin(symbols)].copy()
    if px.empty:
        return None
    px["timestamp"] = pd.to_datetime(px["timestamp"], utc=True)
    wide = {}
    for col in ("open", "high", "low", "close", "volume"):
        wide[col] = px.pivot(index="timestamp", columns="symbol", values=col).sort_index().ffill()
    return wide


def _zscore(x: pd.DataFrame, window: int) -> pd.DataFrame:
    mean = x.shift(1).rolling(window, min_periods=window).mean()
    std = x.shift(1).rolling(window, min_periods=window).std()
    return ((x - mean) / std).replace([np.inf, -np.inf], np.nan)


def _normalize(scores: dict[str, float], output_symbols: list[str], max_abs: float) -> dict[str, float]:
    clean = {s: float(v) for s, v in scores.items() if s in output_symbols and math.isfinite(float(v))}
    if not clean:
        return _zero(output_symbols)
    # Cross-sectional dollar neutrality removes residual market/basket drift.
    vals = pd.Series(clean, dtype=float)
    vals = vals - vals.mean()
    vals = vals.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    gross = float(vals.abs().sum())
    if gross <= 0.0:
        return _zero(output_symbols)
    vals = vals / gross
    vals = vals.clip(lower=-max_abs, upper=max_abs)
    gross = float(vals.abs().sum())
    if gross <= 0.0:
        return _zero(output_symbols)
    vals = vals / gross
    return {s: float(vals.get(s, 0.0)) for s in output_symbols}


def generate_signals(context) -> dict[str, float]:
    """Return target weights for residual overnight-gap continuation.

    Features are computed only from completed daily Alpaca OHLCV bars available
    in context.prices:
    - overnight gap proxy = open / previous close - 1;
    - residual gap = symbol gap minus same-day equal-weight basket gap;
    - residual gap z-score using prior 60 trading days;
    - abnormal volume confirmation using log(volume) z-score;
    - 3-5 day exponentially decayed event score;
    - inverse-volatility scaling and high basket-volatility brake.
    """
    output_symbols = list(context.symbols)
    symbols = [s for s in output_symbols if s in UNIVERSE]
    if len(symbols) < PARAMS.min_symbols or context.prices.empty:
        return _zero(output_symbols)

    wide = _wide(context.prices, symbols)
    if wide is None:
        return _zero(output_symbols)

    open_ = wide["open"].dropna(axis=1, how="any")
    tradable = [s for s in symbols if s in open_.columns]
    required = max(PARAMS.gap_z_window, PARAMS.volume_z_window, PARAMS.market_vol_high_quantile_window) + len(PARAMS.hold_decay) + 2
    if len(tradable) < PARAMS.min_symbols or len(open_) < min(required, PARAMS.gap_z_window + len(PARAMS.hold_decay) + 2):
        return _zero(output_symbols)

    open_ = wide["open"][tradable]
    close = wide["close"][tradable]
    volume = wide["volume"][tradable]

    gap = (open_ / close.shift(1) - 1.0).replace([np.inf, -np.inf], np.nan)
    basket_gap = gap.mean(axis=1)
    residual_gap = gap.sub(basket_gap, axis=0)
    residual_gap_z = _zscore(residual_gap, PARAMS.gap_z_window)

    log_volume = np.log(volume.where(volume > 0))
    volume_z = _zscore(log_volume, PARAMS.volume_z_window)

    close_ret = close.pct_change().replace([np.inf, -np.inf], np.nan)
    vol = close_ret.shift(1).rolling(PARAMS.volatility_window, min_periods=PARAMS.volatility_window).std()
    inv_vol = (1.0 / vol).replace([np.inf, -np.inf], np.nan)
    inv_vol = inv_vol.div(inv_vol.median(axis=1), axis=0).clip(lower=0.50, upper=1.75).fillna(1.0)

    basket_ret = close_ret.mean(axis=1)
    market_vol = basket_ret.rolling(PARAMS.market_vol_window, min_periods=PARAMS.market_vol_window).std()
    vol_rank = market_vol.rolling(PARAMS.market_vol_high_quantile_window, min_periods=60).rank(pct=True)
    latest = close.index[-1]
    brake = PARAMS.high_market_vol_brake if (latest in vol_rank.index and pd.notna(vol_rank.loc[latest]) and float(vol_rank.loc[latest]) > 0.80) else 1.0

    raw = {s: 0.0 for s in output_symbols}
    for age, decay in enumerate(PARAMS.hold_decay):
        event_idx = -1 - age
        if len(residual_gap_z) < abs(event_idx):
            continue
        ts = residual_gap_z.index[event_idx]
        for symbol in tradable:
            rz = residual_gap_z.loc[ts, symbol]
            rg = residual_gap.loc[ts, symbol]
            vz = volume_z.loc[ts, symbol]
            if pd.isna(rz) or pd.isna(rg):
                continue
            rz = float(rz)
            rg = float(rg)
            vz = 0.0 if pd.isna(vz) else float(vz)
            if abs(rz) < PARAMS.entry_residual_gap_z or abs(rg) < PARAMS.min_abs_residual_gap:
                continue
            if vz < PARAMS.abnormal_volume_z:
                continue
            vol_scale = float(inv_vol.loc[ts, symbol]) if symbol in inv_vol.columns and pd.notna(inv_vol.loc[ts, symbol]) else 1.0
            confirmation = 1.0 + 0.15 * min(max(vz - PARAMS.abnormal_volume_z, 0.0), 4.0)
            raw[symbol] += math.copysign((abs(rz) - PARAMS.entry_residual_gap_z) * decay * confirmation * vol_scale * brake, rz)

    return _normalize(raw, output_symbols, PARAMS.max_abs_weight)
