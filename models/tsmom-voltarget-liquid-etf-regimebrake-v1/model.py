"""Regime-braked, turnover-throttled ETF time-series momentum alpha.

qfa contract: expose generate_signals(context) -> dict[str, float].
Consumes only qfa AlphaContext.prices; no external data or state.
"""

from __future__ import annotations

import math

import pandas as pd

DEFAULT_PARAMS = {
    "lookback_days": 126,
    "vol_window": 20,
    "target_vol": 0.10,
    "max_abs_weight": 0.35,
    "min_periods": 127,
    "regime_window": 60,
    "drawdown_brake": 0.10,
    "spy_vol_brake": 0.25,
    "smoothing_alpha": 0.25,
    "max_daily_turnover": 0.50,
}


def _params(context) -> dict:
    metadata = getattr(context, "metadata", {}) or {}
    provided = metadata.get("params", {}) if isinstance(metadata, dict) else {}
    params = DEFAULT_PARAMS.copy()
    params.update({k: provided[k] for k in params.keys() & provided.keys()})
    return params


def _cap_and_renormalize(weights: dict[str, float], cap: float) -> dict[str, float]:
    if not weights:
        return weights
    capped = {symbol: max(min(float(value), cap), -cap) for symbol, value in weights.items()}
    gross = sum(abs(value) for value in capped.values())
    if gross <= 0:
        return {symbol: 0.0 for symbol in capped}
    return {symbol: float(value / gross) for symbol, value in capped.items()}


def _raw_tsmom(close: pd.DataFrame, symbols: list[str], params: dict, end_pos: int) -> dict[str, float]:
    lookback = int(params["lookback_days"])
    vol_window = int(params["vol_window"])
    if end_pos < lookback:
        return {symbol: 0.0 for symbol in symbols}

    trailing_return = close.iloc[end_pos] / close.iloc[end_pos - lookback] - 1.0
    returns = close.iloc[max(0, end_pos - vol_window + 1) : end_pos + 1].pct_change()
    realized_vol = returns.std(ddof=1) * math.sqrt(252)
    realized_vol = realized_vol.replace(0.0, pd.NA).fillna(float(params["target_vol"]))

    raw_scores: dict[str, float] = {}
    for symbol in symbols:
        mom = float(trailing_return.get(symbol, 0.0) or 0.0)
        if mom <= 0:
            raw_scores[symbol] = 0.0
            continue
        vol = float(realized_vol.get(symbol, params["target_vol"]) or params["target_vol"])
        vol_scalar = min(float(params["target_vol"]) / max(vol, 1e-8), 3.0)
        raw_scores[symbol] = mom * vol_scalar

    gross_score = sum(abs(value) for value in raw_scores.values())
    if gross_score <= 0:
        return {symbol: 0.0 for symbol in symbols}
    weights = {symbol: value / gross_score for symbol, value in raw_scores.items()}
    return _cap_and_renormalize(weights, float(params["max_abs_weight"]))


def _regime_risk_off(close: pd.DataFrame, params: dict, end_pos: int) -> bool:
    if "SPY" not in close.columns:
        return False
    regime_window = int(params["regime_window"])
    if end_pos < max(regime_window, int(params["vol_window"])):
        return False
    spy = close["SPY"].iloc[: end_pos + 1].dropna()
    if len(spy) < regime_window + 1:
        return False
    recent = spy.tail(regime_window)
    drawdown = float(spy.iloc[-1] / recent.max() - 1.0)
    spy_vol = float(spy.pct_change().tail(int(params["vol_window"])).std(ddof=1) * math.sqrt(252))
    return drawdown <= -float(params["drawdown_brake"]) or spy_vol >= float(params["spy_vol_brake"])


def _turnover_throttle(prev: dict[str, float], target: dict[str, float], symbols: list[str], max_turnover: float) -> dict[str, float]:
    diff = {symbol: float(target.get(symbol, 0.0)) - float(prev.get(symbol, 0.0)) for symbol in symbols}
    turnover = sum(abs(value) for value in diff.values())
    if turnover <= max_turnover or turnover <= 0:
        return target
    scale = max_turnover / turnover
    return {symbol: float(prev.get(symbol, 0.0)) + diff[symbol] * scale for symbol in symbols}


def generate_signals(context):
    """Return smoothed ETF TSMOM weights, or all-cash (zeros) under SPY stress regime."""
    symbols = list(getattr(context, "symbols", []) or [])
    if not symbols:
        return {}

    params = _params(context)
    prices = getattr(context, "prices", pd.DataFrame()).copy()
    if prices.empty or "timestamp" not in prices or "symbol" not in prices or "close" not in prices:
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

    alpha = float(params["smoothing_alpha"])
    max_turnover = float(params["max_daily_turnover"])
    weights = {symbol: 0.0 for symbol in symbols}
    start_pos = int(params["min_periods"]) - 1

    for end_pos in range(start_pos, len(close)):
        if _regime_risk_off(close, params, end_pos):
            target = {symbol: 0.0 for symbol in symbols}
        else:
            raw = _raw_tsmom(close, symbols, params, end_pos)
            target = {
                symbol: (1.0 - alpha) * float(weights.get(symbol, 0.0)) + alpha * float(raw.get(symbol, 0.0))
                for symbol in symbols
            }
            target = _cap_and_renormalize(target, float(params["max_abs_weight"]))
        weights = _turnover_throttle(weights, target, symbols, max_turnover)
        if sum(abs(value) for value in weights.values()) > 0:
            weights = _cap_and_renormalize(weights, float(params["max_abs_weight"]))

    return {symbol: float(weights.get(symbol, 0.0)) for symbol in symbols}
