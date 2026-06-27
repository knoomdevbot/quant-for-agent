"""Mega-cap tech overnight residual reversal alpha.

QFA contract: expose generate_signals(context) -> dict[symbol, weight].
Research-only model; it never places orders.

Intent: after the market opens, fade idiosyncratic overnight dislocations
(open / prior close - 1 less a rolling-beta market overnight component) and
exit at the same day's close.

Important qfa limitation: qfa's daily backtest invokes generate_signals after a
completed daily bar and applies weights to the next close-to-close return. This
file therefore implements a qfa-compatible lagged proxy. The accompanying
research evaluation uses direct Alpaca daily OHLC bars to simulate the intended
same-day open-to-close holding period without CSV data.
"""

from __future__ import annotations

import math

import pandas as pd


UNIVERSE = ("AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA")


class ModelParams:
    beta_window = 90
    residual_z_window = 60
    entry_z = 0.75
    max_abs_weight = 0.25
    min_symbols = 5


PARAMS = ModelParams()


def _zero_weights(symbols):
    return {symbol: 0.0 for symbol in symbols}


def _cap_and_normalize(weights: dict[str, float], max_abs_weight: float) -> dict[str, float]:
    clean = {s: float(w) for s, w in weights.items() if math.isfinite(float(w))}
    gross = sum(abs(w) for w in clean.values())
    if not clean or gross <= 0.0:
        return {s: 0.0 for s in weights}
    scaled = {s: w / gross for s, w in clean.items()}
    capped = {s: max(-max_abs_weight, min(max_abs_weight, w)) for s, w in scaled.items()}
    capped_gross = sum(abs(w) for w in capped.values())
    if capped_gross <= 0.0:
        return {s: 0.0 for s in weights}
    return {s: float(capped.get(s, 0.0) / capped_gross) for s in weights}


def _wide_ohlc(prices: pd.DataFrame, symbols: list[str]) -> dict[str, pd.DataFrame] | None:
    px = prices[prices["symbol"].isin(symbols)].copy()
    if px.empty:
        return None
    px["timestamp"] = pd.to_datetime(px["timestamp"], utc=True)
    return {
        col: px.pivot(index="timestamp", columns="symbol", values=col).sort_index().ffill()
        for col in ("open", "close")
    }


def _rolling_beta(close_returns: pd.DataFrame, market_returns: pd.Series, window: int) -> pd.DataFrame:
    betas = pd.DataFrame(index=close_returns.index, columns=close_returns.columns, dtype=float)
    market_var = market_returns.rolling(window, min_periods=window).var(ddof=0)
    for symbol in close_returns.columns:
        cov = close_returns[symbol].rolling(window, min_periods=window).cov(market_returns)
        betas[symbol] = cov / market_var
    return betas.shift(1).clip(lower=0.25, upper=2.5)


def generate_signals(context):
    """Return lagged contrarian weights for overnight residual dislocations.

    Signal definition:
    - Compute overnight gap = open / prior close - 1.
    - Estimate each stock's rolling beta to the equal-weight mega-cap tech market
      from prior close-to-close returns.
    - Residual gap = stock overnight gap - beta * market overnight gap.
    - Score latest completed residual gap against prior-only rolling residual
      history; fade residual z-scores whose absolute value exceeds entry_z.
    - De-mean tradable scores, gross-normalize to 1.0, and cap single-name
      absolute exposure at 25%.
    """
    output_symbols = list(context.symbols)
    symbols = [s for s in output_symbols if s in UNIVERSE]
    if len(symbols) < PARAMS.min_symbols or context.prices.empty:
        return _zero_weights(output_symbols)

    wide = _wide_ohlc(context.prices, symbols)
    if wide is None:
        return _zero_weights(output_symbols)

    open_ = wide["open"].dropna(axis=1, how="any")
    close = wide["close"].reindex_like(open_).dropna(axis=1, how="any")
    tradable = [s for s in symbols if s in open_.columns and s in close.columns]
    required = max(PARAMS.beta_window, PARAMS.residual_z_window) + 3
    if len(tradable) < PARAMS.min_symbols or len(close) < required:
        return _zero_weights(output_symbols)

    open_ = open_[tradable]
    close = close[tradable]
    close_ret = close.pct_change()
    market_close_ret = close_ret.mean(axis=1)
    beta = _rolling_beta(close_ret, market_close_ret, PARAMS.beta_window)

    overnight = (open_ / close.shift(1) - 1.0).replace([float("inf"), float("-inf")], pd.NA)
    market_overnight = overnight.mean(axis=1)
    residual = overnight - beta.mul(market_overnight, axis=0)

    resid_mean = residual.shift(1).rolling(PARAMS.residual_z_window, min_periods=PARAMS.residual_z_window).mean()
    resid_std = residual.shift(1).rolling(PARAMS.residual_z_window, min_periods=PARAMS.residual_z_window).std()
    zscore = ((residual - resid_mean) / resid_std).replace([float("inf"), float("-inf")], pd.NA)

    latest = zscore.index[-1]
    raw = {s: 0.0 for s in output_symbols}
    active = {}
    for symbol in tradable:
        z = zscore.loc[latest, symbol]
        if pd.isna(z):
            continue
        z = float(z)
        if abs(z) < PARAMS.entry_z:
            continue
        active[symbol] = -math.copysign(abs(z) - PARAMS.entry_z, z)

    if not active:
        return _zero_weights(output_symbols)
    mean_score = sum(active.values()) / len(active)
    for symbol, score in active.items():
        raw[symbol] = score - mean_score
    return _cap_and_normalize(raw, PARAMS.max_abs_weight)
