"""Macro-shock defensive-sector relative stabilization event-study model.

QFA contract: expose generate_signals(context) -> dict[str, float].
Research-only model: consumes timestamp-safe daily OHLCV in context.prices and
returns target ETF weights. It does not place orders or access live trading APIs.
"""

from __future__ import annotations

import pandas as pd

DEFAULT_PARAMS = {
    "min_periods": 260,
    "shock_lookback_days": 5,
    "hold_days": 5,
    "top_n": 3,
    "sleeve_gross": 0.95,
    "cash_symbol": "SHY",
    "cash_weight": 0.05,
    "defensive_symbols": ("XLP", "XLV", "XLU", "USMV", "SPLV"),
    "cyclical_symbols": ("XLK", "XLY", "XLI", "XLF", "XLE", "XLB", "IWM", "MTUM"),
    "recovery_symbols": ("XLP", "XLV", "XLU", "USMV", "SPLV", "XLRE", "GLD", "TLT", "IEF", "LQD"),
}


def _params(context) -> dict:
    metadata = getattr(context, "metadata", {}) or {}
    provided = metadata.get("params", {}) if isinstance(metadata, dict) else {}
    params = DEFAULT_PARAMS.copy()
    params.update({k: provided[k] for k in params.keys() & provided.keys()})
    return params


def _zero(symbols):
    return {symbol: 0.0 for symbol in symbols}


def generate_signals(context):
    """Return event-gated defensive/recovery ETF weights.

    Timestamp safety: all features use daily bars through the latest supplied
    close. The intended rebalance is at/after that close for the next session.
    The rule activates only when a broad market shock occurred in the prior
    five sessions and defensive assets have stabilized versus cyclicals.
    """
    symbols = list(getattr(context, "symbols", []) or [])
    if not symbols:
        return {}
    params = _params(context)
    prices = getattr(context, "prices", pd.DataFrame()).copy()
    required = {"timestamp", "symbol", "close"}
    if prices.empty or not required.issubset(prices.columns):
        return _zero(symbols)

    prices["timestamp"] = pd.to_datetime(prices["timestamp"], utc=True)
    close = (
        prices[prices["symbol"].isin(symbols)]
        .pivot(index="timestamp", columns="symbol", values="close")
        .sort_index()
        .ffill(limit=3)
        .reindex(columns=symbols)
    )
    close = close.dropna(how="all")
    if len(close) < int(params["min_periods"]):
        return _zero(symbols)

    returns = close.pct_change()
    if "SPY" not in close or "HYG" not in close or "LQD" not in close:
        return _zero(symbols)

    spy = returns["SPY"]
    hyg = returns["HYG"]
    lqd = returns["LQD"]
    vol20 = spy.rolling(20).std() * (252 ** 0.5)
    shock = (
        (spy <= spy.rolling(252, min_periods=126).quantile(0.08))
        | (spy.rolling(3).sum() <= -0.035)
        | ((hyg.rolling(3).sum() <= -0.012) & (spy.rolling(3).sum() <= -0.015))
        | ((vol20 > vol20.rolling(252, min_periods=126).quantile(0.85)) & (spy.rolling(5).sum() < 0.0))
    )

    defensive = [s for s in params["defensive_symbols"] if s in symbols]
    cyclical = [s for s in params["cyclical_symbols"] if s in symbols]
    recovery = [s for s in params["recovery_symbols"] if s in symbols]
    if not defensive or not cyclical or not recovery:
        return _zero(symbols)

    rel_def = returns[defensive].mean(axis=1) - returns[cyclical].mean(axis=1)
    rel3 = rel_def.rolling(3).sum()
    compression = (returns[defensive].abs().mean(axis=1) / (returns[cyclical].abs().mean(axis=1) + 1e-6)).rolling(3).mean()
    credit_confirm = (hyg - lqd).rolling(3).sum() > -0.006
    stabilization = (rel3 > 0.0) & (compression < 1.20) & credit_confirm

    # Active if any stabilization occurred within hold_days after a recent shock.
    lookback = int(params["hold_days"])
    active_signal_idx = None
    for offset in range(0, lookback):
        pos = len(close) - 1 - offset
        if pos < int(params["min_periods"]):
            break
        recent_shock = bool(shock.iloc[max(0, pos - int(params["shock_lookback_days"])) : pos].any())
        if recent_shock and bool(stabilization.iloc[pos]):
            active_signal_idx = pos
            break
    if active_signal_idx is None:
        return _zero(symbols)

    cyc_ret3 = returns[cyclical].mean(axis=1).rolling(3).sum().iloc[active_signal_idx]
    scores = (returns[recovery].rolling(3).sum().iloc[active_signal_idx] - cyc_ret3).dropna()
    selected = list(scores.sort_values(ascending=False).head(max(1, int(params["top_n"]))).index)
    if not selected:
        return _zero(symbols)

    weights = _zero(symbols)
    sleeve = float(params["sleeve_gross"])
    for symbol in selected:
        weights[symbol] = sleeve / len(selected)
    cash = params.get("cash_symbol", "SHY")
    if cash in weights:
        weights[cash] += float(params.get("cash_weight", 0.0))
    return weights
