"""AR-032 cross-sectional ETF dispersion convergence after macro shock days.

QFA contract: expose generate_signals(context) returning target weights.

This is intentionally not a direct single-ETF time-series mean-reversion model.
It waits for a market-wide cross-sectional shock: unusually high dispersion of
same-day ETF returns plus disagreement among SPY/TLT/GLD macro proxies. On such
shock days it takes a next-session convergence basket: long ETFs that lagged the
cross-sectional basket and short ETFs that led it, gross-normalized to 1.0.
"""

from __future__ import annotations

import math

UNIVERSE = ["SPY", "QQQ", "IWM", "TLT", "GLD", "SLV", "XLF", "XLK", "XLE", "XLV"]
DISPERSION_WINDOW = 60
SHOCK_Z = 1.75
MACRO_DISAGREEMENT_Z = 1.0
VOL_WINDOW = 20
MAX_ABS_WEIGHT = 0.20
MIN_HISTORY = max(DISPERSION_WINDOW + 3, VOL_WINDOW + 3)
MACRO_SYMBOLS = ["SPY", "TLT", "GLD"]


def _zero(symbols):
    return {symbol: 0.0 for symbol in symbols}


def _safe_std(series) -> float:
    value = float(series.std(ddof=1)) if len(series) > 1 else float("nan")
    return value if math.isfinite(value) else float("nan")


def _gross_normalize_capped(raw_scores, symbols):
    gross = sum(abs(float(raw_scores.get(symbol, 0.0))) for symbol in symbols)
    if gross <= 0.0:
        return _zero(symbols)
    weights = {symbol: float(raw_scores.get(symbol, 0.0)) / gross for symbol in symbols}
    capped = {symbol: max(-MAX_ABS_WEIGHT, min(MAX_ABS_WEIGHT, weights.get(symbol, 0.0))) for symbol in symbols}
    capped_gross = sum(abs(v) for v in capped.values())
    if capped_gross <= 0.0:
        return _zero(symbols)
    return {symbol: float(capped.get(symbol, 0.0) / capped_gross) for symbol in symbols}


def generate_signals(context):
    """Return next-session convergence weights after cross-sectional shock days."""
    symbols = list(getattr(context, "symbols", []) or [])
    if not symbols:
        return {}

    prices = getattr(context, "prices", None)
    if prices is None or prices.empty:
        return _zero(symbols)
    if not {"timestamp", "symbol", "close"}.issubset(set(prices.columns)):
        return _zero(symbols)

    close = (
        prices[prices["symbol"].isin(symbols)]
        .pivot(index="timestamp", columns="symbol", values="close")
        .sort_index()
        .ffill()
    )
    close = close.dropna(axis=0, how="any")
    if len(close) < MIN_HISTORY:
        return _zero(symbols)

    returns = close.pct_change().dropna()
    if len(returns) < DISPERSION_WINDOW + 1:
        return _zero(symbols)

    latest = returns.iloc[-1]
    trailing = returns.iloc[-DISPERSION_WINDOW:]

    # Cross-sectional return dispersion shock: today's standard deviation across
    # liquid ETFs must be unusually high versus its own trailing history.
    xsec_dispersion = returns.std(axis=1, ddof=1).dropna()
    if len(xsec_dispersion) < DISPERSION_WINDOW:
        return _zero(symbols)
    disp_window = xsec_dispersion.iloc[-DISPERSION_WINDOW:]
    disp_mean = float(disp_window.mean())
    disp_std = _safe_std(disp_window)
    if not math.isfinite(disp_std) or disp_std <= 0.0:
        return _zero(symbols)
    dispersion_z = (float(xsec_dispersion.iloc[-1]) - disp_mean) / disp_std
    if dispersion_z < SHOCK_Z:
        return _zero(symbols)

    # Macro disagreement filter: SPY/TLT/GLD must disagree versus each proxy's
    # own trailing behavior, so the event is broad cross-asset shock absorption
    # rather than a single ETF's stale move.
    available_macro = [symbol for symbol in MACRO_SYMBOLS if symbol in returns.columns]
    if len(available_macro) >= 3:
        macro_zscores = []
        for symbol in available_macro:
            hist = returns[symbol].iloc[-DISPERSION_WINDOW:]
            std = _safe_std(hist)
            if not math.isfinite(std) or std <= 0.0:
                return _zero(symbols)
            macro_zscores.append((float(hist.iloc[-1]) - float(hist.mean())) / std)
        disagreement = max(macro_zscores) - min(macro_zscores)
        if disagreement < MACRO_DISAGREEMENT_Z:
            return _zero(symbols)

    # Convergence basket: cross-sectional de-meaned return residuals. Long the
    # laggards and short the leaders, scaled by inverse recent volatility. This
    # is event-conditioned relative convergence, not univariate z-score reversal.
    cross_mean = float(latest.mean())
    raw = {}
    for symbol in symbols:
        if symbol not in latest.index or symbol not in trailing.columns:
            raw[symbol] = 0.0
            continue
        vol = _safe_std(trailing[symbol].iloc[-VOL_WINDOW:])
        if not math.isfinite(vol) or vol <= 0.0:
            raw[symbol] = 0.0
            continue
        residual = float(latest[symbol]) - cross_mean
        raw[symbol] = -residual / vol

    return _gross_normalize_capped(raw, symbols)
