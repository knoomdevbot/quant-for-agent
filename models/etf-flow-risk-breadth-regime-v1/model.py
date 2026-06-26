"""ETF flow/volume risk breadth regime alpha for qfa.

QFA contract: expose generate_signals(context) -> dict[str, float].
Research-only model; consumes only Alpaca/qfa OHLCV bars and never places orders.

Hypothesis: simultaneous breadth strength and abnormal dollar-volume pressure in
risk-on ETFs versus defensive ETFs proxies allocation pressure into or out of
risk assets. This is intentionally non-calendar and does not use month/turn dates.
"""

from __future__ import annotations

import math

import pandas as pd

RISK_ON = ("SPY", "QQQ", "IWM", "XLF", "XLY", "XLI", "SMH", "HYG")
DEFENSIVE = ("TLT", "IEF", "GLD", "XLU", "XLP", "XLV", "LQD", "SHY")

MIN_PERIODS = 126
BREADTH_LOOKBACK = 20
TREND_LOOKBACK = 63
VOLUME_LOOKBACK = 20
VOL_WINDOW = 20
TOP_N = 4
MAX_ABS_WEIGHT = 0.35
TARGET_VOL = 0.10
RISK_ON_THRESHOLD = 0.08
RISK_OFF_THRESHOLD = -0.04


def _gross_normalize(weights: dict[str, float]) -> dict[str, float]:
    gross = sum(abs(float(v)) for v in weights.values())
    if gross <= 0.0:
        return {symbol: 0.0 for symbol in weights}
    return {symbol: float(v) / gross for symbol, v in weights.items()}


def _cap_and_renormalize(weights: dict[str, float], cap: float) -> dict[str, float]:
    capped = {symbol: max(min(float(value), cap), -cap) for symbol, value in weights.items()}
    return _gross_normalize(capped)


def _safe_zscore(series: pd.Series) -> pd.Series:
    clean = series.replace([float("inf"), float("-inf")], pd.NA).dropna()
    if clean.empty:
        return series * 0.0
    mean = clean.mean()
    std = clean.std(ddof=1)
    if not std or math.isnan(float(std)):
        return series * 0.0
    return (series - mean) / std


def generate_signals(context):
    symbols = list(getattr(context, "symbols", []) or [])
    if not symbols:
        return {}

    prices = getattr(context, "prices", pd.DataFrame()).copy()
    required = {"timestamp", "symbol", "close", "volume"}
    if prices.empty or not required.issubset(prices.columns):
        return {symbol: 0.0 for symbol in symbols}

    prices["timestamp"] = pd.to_datetime(prices["timestamp"], utc=True)
    prices = prices[prices["symbol"].isin(symbols)].sort_values(["timestamp", "symbol"])
    close = prices.pivot(index="timestamp", columns="symbol", values="close").sort_index().ffill()
    volume = prices.pivot(index="timestamp", columns="symbol", values="volume").sort_index().ffill()
    close = close.reindex(columns=symbols).dropna(how="all")
    volume = volume.reindex(columns=symbols).dropna(how="all")

    if len(close) < MIN_PERIODS or len(volume) < MIN_PERIODS:
        return {symbol: 0.0 for symbol in symbols}

    returns = close.pct_change()
    dollar_volume = (close * volume).replace(0.0, pd.NA)

    breadth_lb = min(BREADTH_LOOKBACK, len(close) - 1)
    trend_lb = min(TREND_LOOKBACK, len(close) - 1)
    vol_lb = min(VOL_WINDOW, len(close) - 1)
    if min(breadth_lb, trend_lb, vol_lb) < 2:
        return {symbol: 0.0 for symbol in symbols}

    ret_20 = close.iloc[-1] / close.iloc[-1 - breadth_lb] - 1.0
    ret_63 = close.iloc[-1] / close.iloc[-1 - trend_lb] - 1.0
    realized_vol = (returns.tail(vol_lb).std(ddof=1) * math.sqrt(252)).replace(0.0, pd.NA)
    realized_vol = realized_vol.fillna(TARGET_VOL).clip(lower=0.05)

    dv_now = dollar_volume.tail(5).mean()
    dv_base = dollar_volume.shift(5).tail(VOLUME_LOOKBACK).median().replace(0.0, pd.NA)
    volume_pressure = (dv_now / dv_base - 1.0).replace([float("inf"), float("-inf")], pd.NA).fillna(0.0)

    risk_on = [s for s in RISK_ON if s in symbols and s in close.columns]
    defensive = [s for s in DEFENSIVE if s in symbols and s in close.columns]
    weights = {symbol: 0.0 for symbol in symbols}
    if len(risk_on) < 3 or len(defensive) < 3:
        return weights

    risk_breadth = float((ret_20.reindex(risk_on).dropna() > 0.0).mean())
    def_breadth = float((ret_20.reindex(defensive).dropna() > 0.0).mean())
    risk_flow = float(volume_pressure.reindex(risk_on).dropna().median())
    def_flow = float(volume_pressure.reindex(defensive).dropna().median())
    risk_trend = float((ret_63.reindex(risk_on).dropna() / realized_vol.reindex(risk_on).dropna()).median())
    def_trend = float((ret_63.reindex(defensive).dropna() / realized_vol.reindex(defensive).dropna()).median())

    allocation_pressure = 0.50 * (risk_breadth - def_breadth) + 0.30 * (risk_flow - def_flow) + 0.20 * (risk_trend - def_trend)

    if allocation_pressure > RISK_ON_THRESHOLD:
        candidates = risk_on
        score = 0.45 * _safe_zscore(ret_20) + 0.35 * _safe_zscore(ret_63 / realized_vol) + 0.20 * _safe_zscore(volume_pressure)
    elif allocation_pressure < RISK_OFF_THRESHOLD:
        candidates = defensive
        score = 0.50 * _safe_zscore(ret_20) + 0.30 * _safe_zscore(ret_63 / realized_vol) + 0.20 * _safe_zscore(volume_pressure)
    else:
        # Ambiguous pressure: hold a low-duration defensive sleeve rather than
        # forcing risk exposure. Keeps the signal non-calendar and state-driven.
        candidates = [s for s in ("SHY", "IEF", "GLD", "XLP") if s in defensive]
        score = 0.50 * _safe_zscore(-realized_vol) + 0.30 * _safe_zscore(ret_20) + 0.20 * _safe_zscore(volume_pressure)

    ranked = score.reindex(candidates).replace([float("inf"), float("-inf")], pd.NA).dropna().sort_values(ascending=False)
    selected = list(ranked.head(TOP_N).index)
    if not selected:
        selected = candidates[:TOP_N]
    if not selected:
        return weights

    raw: dict[str, float] = {}
    for symbol in selected:
        vol = float(realized_vol.get(symbol, TARGET_VOL) or TARGET_VOL)
        inv_vol = min(TARGET_VOL / max(vol, 1e-8), 2.5)
        strength = max(float(score.get(symbol, 0.0) or 0.0), 0.0) + 0.25
        raw[symbol] = strength * inv_vol

    weights.update(_cap_and_renormalize(raw, MAX_ABS_WEIGHT))
    return weights
