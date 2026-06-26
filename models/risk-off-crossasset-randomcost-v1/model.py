"""Cost-aware cross-asset risk-on/risk-off switch for liquid ETFs.

QFA contract: expose generate_signals(context) -> dict[str, float].
The model only consumes OHLCV bars supplied by qfa/Alpaca and never places orders.
"""

from __future__ import annotations

import math

import pandas as pd

DEFAULT_PARAMS = {
    "equity_lookback": 100,
    "stress_lookback": 40,
    "vol_window": 20,
    "min_periods": 101,
    "target_vol": 0.10,
    "high_vol_threshold": 0.20,
    "defensive_stress_threshold": 0.03,
    "min_equity_breadth": 0.60,
    "max_abs_weight": 0.35,
    "risk_on_symbols": ("SPY", "QQQ", "IWM", "XLE"),
    "risk_off_symbols": ("TLT", "GLD", "XLU"),
}


def _params(context) -> dict:
    metadata = getattr(context, "metadata", {}) or {}
    provided = metadata.get("params", {}) if isinstance(metadata, dict) else {}
    params = DEFAULT_PARAMS.copy()
    params.update({k: provided[k] for k in params.keys() & provided.keys()})
    return params


def _gross_normalize(weights: dict[str, float]) -> dict[str, float]:
    gross = sum(abs(v) for v in weights.values())
    if gross <= 0.0:
        return {symbol: 0.0 for symbol in weights}
    return {symbol: float(v / gross) for symbol, v in weights.items()}


def _cap_and_renormalize(weights: dict[str, float], cap: float) -> dict[str, float]:
    capped = {symbol: max(min(float(value), cap), -cap) for symbol, value in weights.items()}
    return _gross_normalize(capped)


def _positive(series: pd.Series) -> pd.Series:
    return series.where(series > 0.0, 0.0).fillna(0.0)


def generate_signals(context):
    """Return long-only regime allocation weights by symbol.

    AR-025 refines AR-008 by reducing churn and parameter fragility:
    - slower 100-day equity trend/breadth gate;
    - 40-day TLT/GLD relative-strength stress gate;
    - 20-day SPY realized-volatility throttle;
    - capped per-symbol weights before qfa gross normalization.

    Risk-on regime holds positive momentum among SPY/QQQ/IWM/XLE. Risk-off
    regime holds positive momentum among TLT/GLD/XLU, falling back to equal
    defensive weights when defensive momentum is non-positive. The implementation
    is deterministic and OHLCV-only.
    """
    symbols = list(getattr(context, "symbols", []) or [])
    if not symbols:
        return {}

    params = _params(context)
    prices = getattr(context, "prices", pd.DataFrame()).copy()
    required = {"timestamp", "symbol", "close"}
    if prices.empty or not required.issubset(prices.columns):
        return {symbol: 0.0 for symbol in symbols}

    prices["timestamp"] = pd.to_datetime(prices["timestamp"], utc=True)
    close = (
        prices[prices["symbol"].isin(symbols)]
        .pivot(index="timestamp", columns="symbol", values="close")
        .sort_index()
        .ffill()
    )
    close = close.reindex(columns=symbols).dropna(how="all")
    if len(close) < int(params["min_periods"]):
        return {symbol: 0.0 for symbol in symbols}

    equity_lb = min(int(params["equity_lookback"]), len(close) - 1)
    stress_lb = min(int(params["stress_lookback"]), len(close) - 1)
    vol_window = min(int(params["vol_window"]), len(close) - 1)
    if min(equity_lb, stress_lb, vol_window) < 2:
        return {symbol: 0.0 for symbol in symbols}

    returns = close.pct_change()
    trailing_equity = close.iloc[-1] / close.iloc[-1 - equity_lb] - 1.0
    trailing_stress = close.iloc[-1] / close.iloc[-1 - stress_lb] - 1.0
    realized_vol = returns.tail(vol_window).std(ddof=1) * math.sqrt(252)
    realized_vol = realized_vol.replace(0.0, pd.NA).fillna(float(params["target_vol"]))

    risk_on = [s for s in params["risk_on_symbols"] if s in symbols and s in close.columns]
    risk_off = [s for s in params["risk_off_symbols"] if s in symbols and s in close.columns]
    weights = {symbol: 0.0 for symbol in symbols}
    if not risk_on or not risk_off:
        return weights

    equity_mom = trailing_equity.reindex(risk_on).dropna()
    equity_breadth = float((equity_mom > 0.0).mean()) if len(equity_mom) else 0.0
    spy_mom_long = float(trailing_equity.get("SPY", 0.0) or 0.0)
    spy_mom_stress = float(trailing_stress.get("SPY", 0.0) or 0.0)
    spy_vol = float(realized_vol.get("SPY", params["target_vol"]) or params["target_vol"])

    defensive_rel = []
    for symbol in ("TLT", "GLD"):
        if symbol in close.columns:
            defensive_rel.append(float(trailing_stress.get(symbol, 0.0) or 0.0) - spy_mom_stress)
    defensive_stress = max(defensive_rel) if defensive_rel else 0.0

    risk_on_regime = (
        equity_breadth >= float(params["min_equity_breadth"])
        and spy_mom_long > 0.0
        and spy_vol < float(params["high_vol_threshold"])
        and defensive_stress < float(params["defensive_stress_threshold"])
    )

    target_bucket = risk_on if risk_on_regime else risk_off
    bucket_momentum = _positive(trailing_equity.reindex(target_bucket))
    if bucket_momentum.sum() <= 0.0:
        bucket_momentum = pd.Series(1.0, index=target_bucket, dtype=float)

    raw: dict[str, float] = {}
    for symbol in target_bucket:
        vol = float(realized_vol.get(symbol, params["target_vol"]) or params["target_vol"])
        inv_vol_scale = min(float(params["target_vol"]) / max(vol, 1e-8), 2.0)
        raw[symbol] = float(bucket_momentum.get(symbol, 0.0) * inv_vol_scale)

    if sum(abs(v) for v in raw.values()) <= 0.0:
        raw = {symbol: 1.0 for symbol in target_bucket}

    weights.update(_cap_and_renormalize(raw, float(params["max_abs_weight"])))
    return weights
