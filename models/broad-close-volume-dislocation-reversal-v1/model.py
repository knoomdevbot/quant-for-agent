"""Broad liquid-universe close-volume dislocation reversal.

Research-only qfa model. It uses completed daily OHLCV bars to proxy closing
pressure: abnormal full-day volume plus an extreme close location inside the
session range. Positions are contrarian, inverse-volatility normalized, activated
only on clear dislocation events, and throttled to reduce weak sign-flip turnover.
"""

from __future__ import annotations

import math

import pandas as pd

# Ex-ante liquid large-cap/ETF universe; no return-ranked selection.
UNIVERSE = (
    "SPY", "QQQ", "IWM", "DIA", "XLK", "XLF", "XLE", "XLV", "XLY", "XLI",
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "AVGO", "TSLA", "JPM", "LLY",
    "UNH", "V", "MA", "HD", "COST", "NFLX", "CRM", "AMD", "BAC", "WMT",
    "ORCL", "ADBE", "KO", "PEP", "CSCO", "MCD", "ABT", "TMO", "LIN", "ACN",
)


class ModelParams:
    volume_z_window = 60
    volume_z_min = 1.35
    dollar_volume_z_min = 1.20
    close_location_extreme = 0.86
    range_z_window = 60
    range_z_min = -0.25
    realized_vol_window = 20
    max_market_realized_vol = 0.42
    min_expected_edge_score = 0.12
    strong_fresh_score = 0.22
    flip_dampen = 0.25
    persistence_blend = 0.55
    max_abs_raw_weight = 0.10
    max_etf_gross = 0.35
    min_symbols = 12


PARAMS = ModelParams()
ETFS = {"SPY", "QQQ", "IWM", "DIA", "XLK", "XLF", "XLE", "XLV", "XLY", "XLI"}


def _zero_weights(symbols):
    return {symbol: 0.0 for symbol in symbols}


def _wide_ohlcv(prices: pd.DataFrame, symbols: list[str]):
    px = prices[prices["symbol"].isin(symbols)].copy()
    if px.empty:
        return None
    px["timestamp"] = pd.to_datetime(px["timestamp"], utc=True)
    px = px.sort_values(["timestamp", "symbol"])
    return {col: px.pivot(index="timestamp", columns="symbol", values=col).sort_index().ffill() for col in ("high", "low", "close", "volume")}


def _cap_and_normalize(weights: dict[str, float], max_abs_weight: float, max_etf_gross: float) -> dict[str, float]:
    clean = {s: float(w) for s, w in weights.items() if math.isfinite(float(w))}
    if not clean or sum(abs(w) for w in clean.values()) <= 0.0:
        return {s: 0.0 for s in weights}
    gross = sum(abs(w) for w in clean.values())
    scaled = {s: w / gross for s, w in clean.items()}
    capped = {s: max(-max_abs_weight, min(max_abs_weight, w)) for s, w in scaled.items()}
    etf_gross = sum(abs(capped.get(s, 0.0)) for s in ETFS)
    if etf_gross > max_etf_gross and etf_gross > 0:
        shrink = max_etf_gross / etf_gross
        capped = {s: (w * shrink if s in ETFS else w) for s, w in capped.items()}
    capped_gross = sum(abs(w) for w in capped.values())
    if capped_gross <= 0.0:
        return {s: 0.0 for s in weights}
    return {s: float(capped.get(s, 0.0) / capped_gross) for s in weights}


def _signal_matrix(wide: dict[str, pd.DataFrame], tradable: list[str], params: ModelParams) -> pd.DataFrame:
    close = wide["close"][tradable]
    high = wide["high"][tradable]
    low = wide["low"][tradable]
    volume = wide["volume"][tradable]
    day_range = (high - low).replace(0.0, pd.NA)
    dollar_volume = close * volume
    clv = ((close - low) / day_range).clip(lower=0.0, upper=1.0)
    range_pct = (day_range / close).replace([float("inf"), float("-inf")], pd.NA)

    vol_mean = volume.shift(1).rolling(params.volume_z_window, min_periods=params.volume_z_window).mean()
    vol_std = volume.shift(1).rolling(params.volume_z_window, min_periods=params.volume_z_window).std()
    dvol_mean = dollar_volume.shift(1).rolling(params.volume_z_window, min_periods=params.volume_z_window).mean()
    dvol_std = dollar_volume.shift(1).rolling(params.volume_z_window, min_periods=params.volume_z_window).std()
    range_mean = range_pct.shift(1).rolling(params.range_z_window, min_periods=params.range_z_window).mean()
    range_std = range_pct.shift(1).rolling(params.range_z_window, min_periods=params.range_z_window).std()
    realized_vol = close.pct_change().shift(1).rolling(params.realized_vol_window, min_periods=params.realized_vol_window).std() * (252 ** 0.5)

    vol_z = ((volume - vol_mean) / vol_std.replace(0.0, pd.NA)).replace([float("inf"), float("-inf")], pd.NA)
    dvol_z = ((dollar_volume - dvol_mean) / dvol_std.replace(0.0, pd.NA)).replace([float("inf"), float("-inf")], pd.NA)
    range_z = ((range_pct - range_mean) / range_std.replace(0.0, pd.NA)).replace([float("inf"), float("-inf")], pd.NA)
    inv_vol = (1.0 / realized_vol.replace(0.0, pd.NA)).clip(upper=10.0)

    raw = pd.DataFrame(0.0, index=close.index, columns=tradable)
    for symbol in tradable:
        upper_excess = (clv[symbol] - params.close_location_extreme).clip(lower=0.0)
        lower_excess = ((1.0 - params.close_location_extreme) - clv[symbol]).clip(lower=0.0)
        pressure_side = upper_excess - lower_excess
        volume_confirmation = pd.concat(
            [(vol_z[symbol] - params.volume_z_min).clip(lower=0.0), (dvol_z[symbol] - params.dollar_volume_z_min).clip(lower=0.0)],
            axis=1,
        ).max(axis=1)
        score = pressure_side.abs() * (1.0 + volume_confirmation)
        eligible = (range_z[symbol] >= params.range_z_min) & (volume_confirmation > 0.0) & (score >= params.min_expected_edge_score) & inv_vol[symbol].notna()
        raw.loc[eligible, symbol] = (-pressure_side.loc[eligible] * (1.0 + volume_confirmation.loc[eligible]) * inv_vol.loc[eligible, symbol]).astype(float)

    prev = raw.shift(1).fillna(0.0)
    same_sign = (raw * prev) > 0.0
    strong_fresh = raw.abs() >= params.strong_fresh_score
    adjusted = raw.where(same_sign | strong_fresh, raw * params.flip_dampen)
    adjusted = params.persistence_blend * adjusted + (1.0 - params.persistence_blend) * prev.where(same_sign, 0.0)
    adjusted = adjusted.where(adjusted.abs() >= params.min_expected_edge_score, 0.0)
    return adjusted.fillna(0.0)


def generate_signals(context):
    output_symbols = list(getattr(context, "symbols", []) or [])
    symbols = [s for s in output_symbols if s in UNIVERSE]
    prices = getattr(context, "prices", pd.DataFrame())
    required_rows = max(PARAMS.volume_z_window, PARAMS.range_z_window, PARAMS.realized_vol_window) + 3
    if len(symbols) < PARAMS.min_symbols or prices.empty:
        return _zero_weights(output_symbols)
    wide = _wide_ohlcv(prices, symbols)
    if wide is None:
        return _zero_weights(output_symbols)
    close = wide["close"].dropna(axis=1, how="any")
    tradable = [s for s in symbols if s in close.columns]
    if len(tradable) < PARAMS.min_symbols or len(close) < required_rows:
        return _zero_weights(output_symbols)
    market_vol = float(close[tradable].pct_change().mean(axis=1).tail(PARAMS.realized_vol_window).std() * (252 ** 0.5))
    if not math.isfinite(market_vol) or market_vol > PARAMS.max_market_realized_vol:
        return _zero_weights(output_symbols)
    signals = _signal_matrix(wide, tradable, PARAMS)
    raw = {symbol: 0.0 for symbol in output_symbols}
    latest = signals.index[-1]
    for symbol in tradable:
        raw[symbol] = float(signals.loc[latest, symbol])
    return _cap_and_normalize(raw, PARAMS.max_abs_raw_weight, PARAMS.max_etf_gross)
