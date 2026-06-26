"""Cross-asset ETF volatility-regime rotation alpha for qfa.

Research-only qfa contract: generate_signals(context) -> dict[str, float].
This model uses completed daily OHLCV bars only and rotates across liquid ETFs
based on realized-volatility regime, cross-asset breadth, and defensive asset
confirmation. It is deliberately unrelated to overnight gap reversal mechanics.
"""

from __future__ import annotations

import math

import pandas as pd

DEFAULT_PARAMS = {
    "vol_fast_window": 20,
    "vol_slow_window": 60,
    "breadth_window": 60,
    "drawdown_window": 63,
    "momentum_window": 63,
    "risk_budget_low": 0.55,
    "risk_budget_high": 1.00,
    "top_n": 3,
    "max_abs_weight": 0.45,
    "risk_on_symbols": ("SPY", "QQQ", "IWM", "XLK", "XLF", "XLE", "XLV"),
    "defensive_symbols": ("TLT", "GLD", "SLV", "XLV"),
}


def _params(context) -> dict:
    metadata = getattr(context, "metadata", {}) or {}
    provided = metadata.get("params", {}) if isinstance(metadata, dict) else {}
    params = DEFAULT_PARAMS.copy()
    params.update({k: provided[k] for k in params.keys() & provided.keys()})
    return params


def _normalize_capped(raw: dict[str, float], cap: float) -> dict[str, float]:
    if not raw:
        return {}
    capped = {symbol: max(min(float(value), cap), -cap) for symbol, value in raw.items()}
    gross = sum(abs(value) for value in capped.values())
    if gross <= 0.0:
        return {symbol: 0.0 for symbol in capped}
    return {symbol: float(value / gross) for symbol, value in capped.items()}


def generate_signals(context):
    """Return long-only ETF rotation weights.

    Regime mechanics:
    - compute 20-day versus 60-day realized-volatility pressure for SPY/QQQ/IWM;
    - compute 60-day breadth across all available ETFs and a 63-day SPY drawdown;
    - risk-on when breadth is broad, SPY drawdown is contained, and equity vol is
      not spiking; otherwise rotate into defensive ETFs with positive relative
      strength; and
    - rank candidates by momentum divided by recent realized volatility.
    """
    symbols = list(getattr(context, "symbols", []) or [])
    if not symbols:
        return {}

    params = _params(context)
    weights = {symbol: 0.0 for symbol in symbols}
    prices = getattr(context, "prices", pd.DataFrame()).copy()
    required = {"timestamp", "symbol", "close"}
    if prices.empty or not required.issubset(prices.columns):
        return weights

    prices["timestamp"] = pd.to_datetime(prices["timestamp"], utc=True)
    close = (
        prices[prices["symbol"].isin(symbols)]
        .pivot(index="timestamp", columns="symbol", values="close")
        .sort_index()
        .ffill()
    )
    close = close.reindex(columns=symbols).dropna(how="all")
    min_history = max(
        int(params["vol_slow_window"]),
        int(params["breadth_window"]),
        int(params["drawdown_window"]),
        int(params["momentum_window"]),
    ) + 2
    if len(close) < min_history:
        return weights

    returns = close.pct_change()
    vol_fast_window = min(int(params["vol_fast_window"]), len(close) - 1)
    vol_slow_window = min(int(params["vol_slow_window"]), len(close) - 1)
    breadth_window = min(int(params["breadth_window"]), len(close) - 1)
    drawdown_window = min(int(params["drawdown_window"]), len(close) - 1)
    momentum_window = min(int(params["momentum_window"]), len(close) - 1)

    fast_vol = (returns.tail(vol_fast_window).std(ddof=1) * math.sqrt(252)).replace(0.0, pd.NA)
    slow_vol = (returns.tail(vol_slow_window).std(ddof=1) * math.sqrt(252)).replace(0.0, pd.NA)
    vol_ratio = (fast_vol / slow_vol).replace([float("inf"), float("-inf")], pd.NA)

    momentum = close.iloc[-1] / close.iloc[-1 - momentum_window] - 1.0
    breadth_momentum = close.iloc[-1] / close.iloc[-1 - breadth_window] - 1.0
    breadth = float((breadth_momentum.dropna() > 0.0).mean()) if len(breadth_momentum.dropna()) else 0.0

    spy_series = close["SPY"].dropna() if "SPY" in close.columns else pd.Series(dtype=float)
    spy_drawdown = 0.0
    spy_momentum = 0.0
    if len(spy_series) > drawdown_window:
        trailing = spy_series.tail(drawdown_window + 1)
        spy_drawdown = float(spy_series.iloc[-1] / trailing.max() - 1.0)
        spy_momentum = float(momentum.get("SPY", 0.0) or 0.0)

    equity_regime_symbols = [s for s in ("SPY", "QQQ", "IWM") if s in symbols and s in vol_ratio.index]
    equity_vol_ratio = float(vol_ratio.reindex(equity_regime_symbols).dropna().median()) if equity_regime_symbols else 1.0
    defensive_alignment = 0
    for defensive in ("TLT", "GLD"):
        if defensive in momentum.index and float(momentum.get(defensive, 0.0) or 0.0) > spy_momentum:
            defensive_alignment += 1

    risk_on = (breadth >= 0.55) and (spy_drawdown > -0.10) and (equity_vol_ratio <= 1.25)
    risk_on_names = [s for s in params["risk_on_symbols"] if s in symbols]
    defensive_names = [s for s in params["defensive_symbols"] if s in symbols]
    if (not risk_on) or defensive_alignment >= 1:
        candidate_symbols = defensive_names
        budget = float(params["risk_budget_low"])
    else:
        candidate_symbols = risk_on_names
        budget = float(params["risk_budget_high"])

    realized_vol = fast_vol.fillna(slow_vol).fillna(0.20).clip(lower=0.03)
    score = (momentum / realized_vol).replace([float("inf"), float("-inf")], pd.NA).dropna()
    ranked = score.reindex(candidate_symbols).dropna().sort_values(ascending=False)
    selected = list(ranked.head(max(1, int(params["top_n"]))).index)
    if not selected:
        selected = candidate_symbols[: max(1, int(params["top_n"]))]
    if not selected:
        return weights

    raw: dict[str, float] = {}
    for symbol in selected:
        mom = float(momentum.get(symbol, 0.0) or 0.0)
        vol = float(realized_vol.get(symbol, 0.20) or 0.20)
        # In stressed regimes allow defensive winners even if their absolute
        # momentum is only mildly positive; do not short laggards.
        raw[symbol] = max(mom, 0.0) / max(vol, 1e-8) + 0.02

    normalized = _normalize_capped(raw, float(params["max_abs_weight"]))
    # qfa normalizes non-zero gross to one, so the budget affects relative raw
    # aggressiveness for portability but qfa backtest metrics are full-gross.
    for symbol, value in normalized.items():
        weights[symbol] = float(value * budget)
    return weights
