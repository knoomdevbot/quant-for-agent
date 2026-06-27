"""AR-075 sector ETF dispersion-dislocation mean reversion.

QFA contract: expose generate_signals(context) -> dict[symbol, weight].
Uses only OHLCV bars supplied by qfa/Alpaca. No CSV, daemon, or orders.

Mechanism: after unusually wide cross-sectional sector residual dispersion, fade
short-horizon sector moves residualized to SPY while keeping broad-market beta
small. This is deliberately a sector relative-value liquidity-provision signal,
not defensive carry allocation or univariate ETF mean reversion.
"""
from __future__ import annotations

import math

import pandas as pd

UNIVERSE = ["SPY", "QQQ", "IWM", "XLF", "XLK", "XLE", "XLU", "XLV", "XLI", "XLP"]
SECTORS = ["XLF", "XLK", "XLE", "XLU", "XLV", "XLI", "XLP"]
BROAD = "SPY"
PARAMS = {
    "residual_lookback": 5,
    "beta_window": 60,
    "dispersion_window": 63,
    "vol_window": 20,
    "trend_window": 100,
    "min_history": 130,
    "dispersion_z_entry": 0.80,
    "residual_z_entry": 0.55,
    "max_gross": 1.0,
    "sector_cap": 0.24,
    "broad_hedge_cap": 0.35,
    "trend_dampen_threshold": 0.12,
}


def _zero(symbols: list[str]) -> dict[str, float]:
    return {s: 0.0 for s in symbols}


def _safe_std(x: pd.Series) -> float:
    v = float(x.dropna().std(ddof=1)) if len(x.dropna()) > 1 else float("nan")
    return v if math.isfinite(v) and v > 0 else float("nan")


def _close_matrix(context) -> pd.DataFrame:
    prices = getattr(context, "prices", None)
    symbols = list(getattr(context, "symbols", []) or [])
    if prices is None or prices.empty or not {"timestamp", "symbol", "close"}.issubset(prices.columns):
        return pd.DataFrame()
    p = prices[prices["symbol"].isin([s for s in UNIVERSE if s in symbols])].copy()
    if p.empty:
        return pd.DataFrame()
    p["timestamp"] = pd.to_datetime(p["timestamp"], utc=True)
    close = p.pivot(index="timestamp", columns="symbol", values="close").sort_index().ffill()
    return close.dropna(axis=1, how="all")


def _cap_and_normalize(raw: dict[str, float], symbols: list[str]) -> dict[str, float]:
    capped = {}
    for s in symbols:
        cap = PARAMS["broad_hedge_cap"] if s == BROAD else PARAMS["sector_cap"]
        capped[s] = max(-cap, min(cap, float(raw.get(s, 0.0))))
    gross = sum(abs(v) for v in capped.values())
    if gross <= 0:
        return _zero(symbols)
    scale = min(1.0, PARAMS["max_gross"] / gross)
    return {s: float(capped[s] * scale) for s in symbols}


def generate_signals(context) -> dict[str, float]:
    """Return target weights for next daily bar."""
    symbols = list(getattr(context, "symbols", []) or [])
    if not symbols:
        return {}
    close = _close_matrix(context)
    sectors = [s for s in SECTORS if s in close.columns and s in symbols]
    if BROAD not in close.columns or len(sectors) < 5 or len(close) < PARAMS["min_history"]:
        return _zero(symbols)

    ret = close[[BROAD] + sectors].pct_change().dropna(how="any")
    p = PARAMS
    if len(ret) < max(p["beta_window"], p["dispersion_window"], p["trend_window"]) + p["residual_lookback"]:
        return _zero(symbols)

    spy = ret[BROAD]
    residual_scores: dict[str, float] = {}
    beta_est: dict[str, float] = {}
    residual_matrix = []
    for sector in sectors:
        cov = ret[sector].iloc[-p["beta_window"] :].cov(spy.iloc[-p["beta_window"] :])
        var = spy.iloc[-p["beta_window"] :].var(ddof=1)
        beta = float(cov / var) if var and math.isfinite(float(var)) else 1.0
        beta = max(0.25, min(1.75, beta))
        beta_est[sector] = beta
        # Build trailing residual return sums for dispersion-normalization.
        residual_daily = ret[sector] - beta * spy
        roll_resid = residual_daily.rolling(p["residual_lookback"]).sum().dropna()
        if len(roll_resid) < p["dispersion_window"]:
            continue
        recent = float(roll_resid.iloc[-1])
        vol = _safe_std(residual_daily.iloc[-p["vol_window"] :])
        if not math.isfinite(vol):
            continue
        residual_scores[sector] = recent / (vol * math.sqrt(p["residual_lookback"]))
        residual_matrix.append(roll_resid)

    if len(residual_scores) < 5:
        return _zero(symbols)

    # Is current residual cross-section unusually dispersed versus history?
    zhist = pd.concat(residual_matrix, axis=1).dropna()
    if len(zhist) < p["dispersion_window"]:
        return _zero(symbols)
    xdisp = zhist.std(axis=1, ddof=1).dropna()
    dwin = xdisp.iloc[-p["dispersion_window"] :]
    dsd = _safe_std(dwin)
    if not math.isfinite(dsd):
        return _zero(symbols)
    dispersion_z = (float(xdisp.iloc[-1]) - float(dwin.mean())) / dsd
    if dispersion_z < p["dispersion_z_entry"]:
        return _zero(symbols)

    vals = pd.Series(residual_scores).dropna()
    cross_sd = _safe_std(vals)
    if not math.isfinite(cross_sd):
        return _zero(symbols)
    center = float(vals.mean())
    raw_sector = {}
    for sector, val in residual_scores.items():
        z = (float(val) - center) / cross_sd
        # Fade only meaningful sector dislocations; leave small residuals flat to reduce turnover.
        raw_sector[sector] = -z if abs(z) >= p["residual_z_entry"] else 0.0

    gross_signal = sum(abs(v) for v in raw_sector.values())
    if gross_signal <= 0:
        return _zero(symbols)

    # Dampen in strong broad trends, where sector dislocations often continue.
    spy_trend = float(close[BROAD].iloc[-1] / close[BROAD].iloc[-p["trend_window"]] - 1.0)
    trend_scale = 0.55 if abs(spy_trend) > p["trend_dampen_threshold"] else 1.0

    raw = {s: 0.0 for s in symbols}
    for sector, score in raw_sector.items():
        raw[sector] = trend_scale * score / gross_signal

    # Add SPY hedge to reduce estimated broad beta of sector basket.
    sector_beta = sum(raw.get(s, 0.0) * beta_est.get(s, 1.0) for s in sectors)
    if BROAD in symbols:
        raw[BROAD] = max(-p["broad_hedge_cap"], min(p["broad_hedge_cap"], -sector_beta))

    return _cap_and_normalize(raw, symbols)
