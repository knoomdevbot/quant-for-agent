"""
AR-116 concentration-breadth mean-reversion allocator.

Research-only qfa-compatible model. It consumes only completed daily OHLCV bars
provided in context.prices (qfa/Alpaca) and returns target weights. No orders are
placed. The rule is fixed ex ante: when cap-weight leadership (QQQ/SPY and a
fixed mega-cap signal basket) is unusually stretched versus equal-weight/breadth
proxies (RSP, QQQE, IWM), and a simple OHLCV crisis brake is inactive, allocate
toward equal-weight/breadth ETFs with modest beta-reduced shorts in cap-weight
leadership sleeves. Otherwise hold no exposure.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

PRIMARY_SYMBOLS = ("SPY", "QQQ", "RSP", "QQQE", "IWM", "SHY")
MEGACAP_SIGNAL = ("AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA")
MIN_HISTORY = 252
REL_MOM_LOOKBACK = 20
ZSCORE_LOOKBACK = 60
CRISIS_VOL_LOOKBACK = 20
CRISIS_VOL_QUANTILE_LOOKBACK = 504
STRETCH_THRESHOLD = 1.25
STRONG_STRETCH_THRESHOLD = 2.00
MAX_GROSS = 1.0


def _zscore_last(series: pd.Series, lookback: int) -> float:
    window = series.dropna().tail(lookback)
    if len(window) < max(20, lookback // 2):
        return np.nan
    sd = float(window.std(ddof=0))
    if sd <= 1e-12 or not np.isfinite(sd):
        return np.nan
    return float((window.iloc[-1] - window.mean()) / sd)


def _safe_rel_mom(close: pd.DataFrame, lhs: str, rhs: str) -> pd.Series:
    if lhs not in close or rhs not in close:
        return pd.Series(index=close.index, dtype=float)
    return np.log(close[lhs] / close[rhs]).diff(REL_MOM_LOOKBACK)


def _megacap_basket(close: pd.DataFrame) -> pd.Series | None:
    available = [s for s in MEGACAP_SIGNAL if s in close and close[s].dropna().shape[0] >= MIN_HISTORY]
    if len(available) < 5:
        return None
    normalized = close[available].ffill() / close[available].ffill().iloc[0]
    return normalized.mean(axis=1)


def _weights_from_history(prices: pd.DataFrame, as_of: Any | None = None) -> dict[str, float]:
    if prices is None or prices.empty:
        return {}
    bars = prices.copy()
    bars["timestamp"] = pd.to_datetime(bars["timestamp"], utc=True)
    if as_of is not None:
        ts = pd.Timestamp(as_of)
        ts = ts.tz_convert("UTC") if ts.tzinfo else ts.tz_localize("UTC")
        bars = bars[bars["timestamp"] <= ts]
    if bars.empty:
        return {}

    close = bars.pivot(index="timestamp", columns="symbol", values="close").sort_index().ffill()
    if close.shape[0] < MIN_HISTORY or not {"SPY", "QQQ", "RSP", "IWM"}.issubset(close.columns):
        return {}

    rets = close.pct_change()
    spy_vol20 = rets["SPY"].rolling(CRISIS_VOL_LOOKBACK).std() * np.sqrt(252)
    vol_q90 = spy_vol20.rolling(CRISIS_VOL_QUANTILE_LOOKBACK, min_periods=126).quantile(0.90)
    spy_dd20 = close["SPY"] / close["SPY"].rolling(20).max() - 1.0
    crisis = bool((spy_vol20.iloc[-1] > vol_q90.iloc[-1]) or (spy_dd20.iloc[-1] < -0.08)) if np.isfinite(vol_q90.iloc[-1]) else bool(spy_dd20.iloc[-1] < -0.08)
    if crisis:
        return {}

    features: list[float] = []
    for lhs, rhs in (("QQQ", "RSP"), ("SPY", "RSP"), ("QQQ", "IWM"), ("QQQ", "QQQE")):
        z = _zscore_last(_safe_rel_mom(close, lhs, rhs), ZSCORE_LOOKBACK)
        if np.isfinite(z):
            features.append(z)
    basket = _megacap_basket(close)
    if basket is not None and "RSP" in close:
        rel = np.log(basket / close["RSP"]).diff(REL_MOM_LOOKBACK)
        z = _zscore_last(rel, ZSCORE_LOOKBACK)
        if np.isfinite(z):
            features.append(z)
    if len(features) < 3:
        return {}
    stretch = float(np.nanmean(features))
    if stretch < STRETCH_THRESHOLD:
        return {}

    rsp_vs_spy_20 = float(close["RSP"].pct_change(20).iloc[-1] - close["SPY"].pct_change(20).iloc[-1])
    iwm_vs_qqq_20 = float(close["IWM"].pct_change(20).iloc[-1] - close["QQQ"].pct_change(20).iloc[-1])
    breadth_lag_confirmed = (rsp_vs_spy_20 < 0.01) or (iwm_vs_qqq_20 < 0.01)
    if not breadth_lag_confirmed:
        return {}

    if stretch >= STRONG_STRETCH_THRESHOLD:
        raw = {"RSP": 0.36, "QQQE": 0.24, "IWM": 0.20, "QQQ": -0.12, "SPY": -0.08}
    else:
        raw = {"RSP": 0.34, "QQQE": 0.18, "IWM": 0.16, "QQQ": -0.08, "SPY": -0.04}
    if "QQQE" not in close or close["QQQE"].dropna().shape[0] < MIN_HISTORY:
        qqqe_w = raw.pop("QQQE", 0.0)
        raw["RSP"] = raw.get("RSP", 0.0) + 0.70 * qqqe_w
        raw["IWM"] = raw.get("IWM", 0.0) + 0.30 * qqqe_w
    gross = sum(abs(v) for v in raw.values())
    if gross <= 0:
        return {}
    scale = min(MAX_GROSS / gross, 1.0)
    return {k: float(v * scale) for k, v in raw.items() if abs(v * scale) > 1e-6}


def generate_signals(context: Any) -> dict[str, float]:
    return _weights_from_history(context.prices, getattr(context, "as_of", None))
