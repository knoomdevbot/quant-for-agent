"""Orthogonality-constrained close-location/abnormal-volume reversal.

QFA contract: expose generate_signals(context) -> dict[str, float].
Research-only model; it does not place orders.

This AR-056 refinement of AR-045 attempts to reduce broad market/AR-028 overlap by:
- requiring an abnormal close-location event with abnormal volume/dollar-volume;
- confirming the event with same-direction idiosyncratic return residual versus the
  equal-weight mega-cap basket;
- suppressing high basket-volatility/high basket-move regimes where broad beta
  dominates close-location reversal;
- beta-neutralizing raw scores and enforcing near dollar-neutral normalized weights;
- retaining AR-045-style turnover dampening and volatility-normalized sizing.

Alpaca/qfa daily OHLCV has no true closing-auction imbalance, so this remains a
completed-daily-bar proxy for next-session close-to-close reversal.
"""

from __future__ import annotations

import math

import pandas as pd

UNIVERSE = ("AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "AVGO", "TSLA", "JPM", "LLY")


class ModelParams:
    volume_z_window = 60
    volume_z_min = 1.75
    dollar_volume_z_min = 1.75
    close_location_extreme = 0.86
    range_z_window = 60
    range_z_min = 0.10
    realized_vol_window = 20
    residual_beta_window = 60
    residual_z_window = 60
    residual_z_min = 0.40
    max_market_realized_vol = 0.32
    max_abs_market_move = 0.018
    min_expected_edge_score = 0.13
    strong_fresh_score = 0.30
    flip_dampen = 0.25
    persistence_blend = 0.55
    beta_neutral_strength = 0.80
    max_abs_raw_weight = 0.22
    min_symbols = 5


PARAMS = ModelParams()


def _zero_weights(symbols):
    return {symbol: 0.0 for symbol in symbols}


def _wide_ohlcv(prices: pd.DataFrame, symbols: list[str]):
    px = prices[prices["symbol"].isin(symbols)].copy()
    if px.empty:
        return None
    px["timestamp"] = pd.to_datetime(px["timestamp"], utc=True)
    px = px.sort_values(["timestamp", "symbol"])
    wide = {}
    for col in ("high", "low", "close", "volume"):
        wide[col] = px.pivot(index="timestamp", columns="symbol", values=col).sort_index().ffill()
    return wide


def _cap_and_neutral_normalize(weights: dict[str, float], max_abs_weight: float) -> dict[str, float]:
    clean = {s: float(w) for s, w in weights.items() if math.isfinite(float(w))}
    if not clean:
        return {s: 0.0 for s in weights}
    mean_weight = sum(clean.values()) / max(len(clean), 1)
    neutral = {s: w - mean_weight for s, w in clean.items()}
    gross = sum(abs(w) for w in neutral.values())
    if gross <= 0.0:
        return {s: 0.0 for s in weights}
    scaled = {s: w / gross for s, w in neutral.items()}
    capped = {s: max(-max_abs_weight, min(max_abs_weight, w)) for s, w in scaled.items()}
    capped_mean = sum(capped.values()) / max(len(capped), 1)
    capped = {s: w - capped_mean for s, w in capped.items()}
    capped_gross = sum(abs(w) for w in capped.values())
    if capped_gross <= 0.0:
        return {s: 0.0 for s in weights}
    return {s: float(capped.get(s, 0.0) / capped_gross) for s in weights}


def _rolling_residuals(close: pd.DataFrame, params: ModelParams):
    returns = close.pct_change()
    market = returns.mean(axis=1)
    market_var = market.shift(1).rolling(params.residual_beta_window, min_periods=params.residual_beta_window).var()
    betas = pd.DataFrame(index=returns.index, columns=returns.columns, dtype=float)
    for symbol in returns.columns:
        cov = returns[symbol].shift(1).rolling(params.residual_beta_window, min_periods=params.residual_beta_window).cov(market.shift(1))
        betas[symbol] = (cov / market_var.replace(0.0, pd.NA)).clip(lower=-1.0, upper=3.0)
    residual = returns - betas.multiply(market, axis=0)
    resid_mean = residual.shift(1).rolling(params.residual_z_window, min_periods=params.residual_z_window).mean()
    resid_std = residual.shift(1).rolling(params.residual_z_window, min_periods=params.residual_z_window).std()
    resid_z = ((residual - resid_mean) / resid_std.replace(0.0, pd.NA)).replace([float("inf"), float("-inf")], pd.NA)
    return residual, resid_z, betas


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
    residual, resid_z, betas = _rolling_residuals(close, params)

    vol_z = ((volume - vol_mean) / vol_std.replace(0.0, pd.NA)).replace([float("inf"), float("-inf")], pd.NA)
    dvol_z = ((dollar_volume - dvol_mean) / dvol_std.replace(0.0, pd.NA)).replace([float("inf"), float("-inf")], pd.NA)
    range_z = ((range_pct - range_mean) / range_std.replace(0.0, pd.NA)).replace([float("inf"), float("-inf")], pd.NA)

    raw = pd.DataFrame(0.0, index=close.index, columns=tradable)
    inv_vol = (1.0 / realized_vol.replace(0.0, pd.NA)).clip(upper=10.0)
    for symbol in tradable:
        upper_excess = (clv[symbol] - params.close_location_extreme).clip(lower=0.0)
        lower_excess = ((1.0 - params.close_location_extreme) - clv[symbol]).clip(lower=0.0)
        pressure_side = upper_excess - lower_excess  # positive close-at-high pressure; reversal wants short
        volume_confirmation = pd.concat(
            [
                (vol_z[symbol] - params.volume_z_min).clip(lower=0.0),
                (dvol_z[symbol] - params.dollar_volume_z_min).clip(lower=0.0),
            ],
            axis=1,
        ).max(axis=1)
        residual_confirm = (pressure_side * resid_z[symbol]) > params.residual_z_min
        score = pressure_side.abs() * (1.0 + volume_confirmation) * (1.0 + resid_z[symbol].abs().clip(upper=2.5) / 3.0)
        eligible = (
            (range_z[symbol] >= params.range_z_min)
            & (volume_confirmation > 0.0)
            & residual_confirm
            & (score >= params.min_expected_edge_score)
            & inv_vol[symbol].notna()
        )
        raw.loc[eligible, symbol] = (-pressure_side.loc[eligible] * (1.0 + volume_confirmation.loc[eligible]) * inv_vol.loc[eligible, symbol]).astype(float)

    # Reduce same-day basket beta exposure from the raw score vector using rolling betas.
    beta_adjusted = raw.copy()
    for idx in raw.index:
        row = raw.loc[idx].astype(float)
        gross = row.abs().sum()
        if gross <= 0.0:
            continue
        beta_row = betas.loc[idx].astype(float).fillna(1.0)
        denom = float((beta_row * beta_row).sum())
        if denom > 0.0:
            beta_exposure = float((row * beta_row).sum())
            beta_adjusted.loc[idx] = row - params.beta_neutral_strength * beta_exposure * beta_row / denom

    prev = beta_adjusted.shift(1).fillna(0.0)
    same_sign = (beta_adjusted * prev) > 0.0
    strong_fresh = beta_adjusted.abs() >= params.strong_fresh_score
    adjusted = beta_adjusted.where(same_sign | strong_fresh, beta_adjusted * params.flip_dampen)
    adjusted = params.persistence_blend * adjusted + (1.0 - params.persistence_blend) * prev.where(same_sign, 0.0)
    adjusted = adjusted.where(adjusted.abs() >= params.min_expected_edge_score, 0.0)
    # Cross-sectionally demean to reduce equal-weight/market exposure before final qfa normalization.
    adjusted = adjusted.sub(adjusted.mean(axis=1), axis=0)
    return adjusted.fillna(0.0)


def generate_signals(context):
    """Return orthogonalized contrarian target weights for context.symbols."""
    output_symbols = list(getattr(context, "symbols", []) or [])
    symbols = [s for s in output_symbols if s in UNIVERSE]
    required_rows = max(PARAMS.volume_z_window, PARAMS.range_z_window, PARAMS.residual_beta_window + PARAMS.residual_z_window, PARAMS.realized_vol_window) + 3
    prices = getattr(context, "prices", pd.DataFrame())
    if len(symbols) < PARAMS.min_symbols or prices.empty:
        return _zero_weights(output_symbols)

    wide = _wide_ohlcv(prices, symbols)
    if wide is None:
        return _zero_weights(output_symbols)
    close = wide["close"].dropna(axis=1, how="any")
    tradable = [s for s in symbols if s in close.columns]
    if len(tradable) < PARAMS.min_symbols or len(close) < required_rows:
        return _zero_weights(output_symbols)

    market_returns = close[tradable].pct_change().mean(axis=1)
    recent_market_vol = float(market_returns.tail(PARAMS.realized_vol_window).std() * (252 ** 0.5)) if len(market_returns.dropna()) >= PARAMS.realized_vol_window else 999.0
    last_market_move = float(market_returns.iloc[-1]) if len(market_returns.dropna()) else 999.0
    if (
        not math.isfinite(recent_market_vol)
        or recent_market_vol > PARAMS.max_market_realized_vol
        or not math.isfinite(last_market_move)
        or abs(last_market_move) > PARAMS.max_abs_market_move
    ):
        return _zero_weights(output_symbols)

    signals = _signal_matrix(wide, tradable, PARAMS)
    latest = signals.index[-1]
    raw = {symbol: 0.0 for symbol in output_symbols}
    for symbol in tradable:
        raw[symbol] = float(signals.loc[latest, symbol])
    return _cap_and_neutral_normalize(raw, PARAMS.max_abs_raw_weight)
