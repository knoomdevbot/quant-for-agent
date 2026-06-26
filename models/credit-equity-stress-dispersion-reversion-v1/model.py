"""AR-044 credit/equity stress dispersion mean-reversion model.

QFA contract: expose generate_signals(context) -> dict[str, float].
Research-only: consumes daily OHLCV in context.prices and never places orders.
"""
from __future__ import annotations

import math

import pandas as pd

DEFAULT_PARAMS = {
    "lookback": 7,
    "confirm_window": 2,
    "vol_window": 20,
    "min_periods": 45,
    "entry_z": 1.05,
    "exit_z": 0.20,
    "vol_ceiling": 0.34,
    "target_vol": 0.10,
    "max_symbol_abs_weight": 0.28,
    "equity_symbols": ("SPY", "QQQ", "IWM"),
    "credit_symbols": ("HYG", "LQD"),
    "defensive_symbols": ("TLT", "GLD", "XLU"),
}


def _params(context) -> dict:
    metadata = getattr(context, "metadata", {}) or {}
    provided = metadata.get("params", {}) if isinstance(metadata, dict) else {}
    params = DEFAULT_PARAMS.copy()
    params.update({k: provided[k] for k in params.keys() & provided.keys()})
    return params


def _safe_group(cols, available):
    return [s for s in cols if s in available]


def _normalize(raw: dict[str, float], symbols: list[str], cap: float) -> dict[str, float]:
    capped = {s: max(min(float(raw.get(s, 0.0)), cap), -cap) for s in symbols}
    gross = sum(abs(v) for v in capped.values())
    if gross <= 0:
        return {s: 0.0 for s in symbols}
    return {s: float(v / gross) for s, v in capped.items()}


def generate_signals(context):
    """Return target weights for cross-asset stress-dispersion reversion.

    Signal mechanics:
    - compute 7-day returns for equity beta ETFs versus credit/defensive proxies;
    - standardize the equity-minus-credit/defensive dispersion over a short history;
    - if equities have underperformed credit/defensive assets by a large amount and
      the last 1-2 daily bars show stabilization, go long equities and short the
      stress/defensive basket;
    - if equities have outperformed sharply while credit/defensive ETFs stabilize,
      take the opposite convergence trade;
    - stand aside when SPY realized vol is above the stress ceiling.
    """
    symbols = list(getattr(context, "symbols", []) or [])
    if not symbols:
        return {}
    weights0 = {s: 0.0 for s in symbols}
    params = _params(context)
    prices = getattr(context, "prices", pd.DataFrame()).copy()
    required = {"timestamp", "symbol", "close"}
    if prices.empty or not required.issubset(prices.columns):
        return weights0

    prices["timestamp"] = pd.to_datetime(prices["timestamp"], utc=True)
    close = (
        prices[prices["symbol"].isin(symbols)]
        .pivot(index="timestamp", columns="symbol", values="close")
        .sort_index()
        .ffill()
    )
    close = close.reindex(columns=symbols).dropna(how="all")
    min_periods = int(params["min_periods"])
    lookback = int(params["lookback"])
    if len(close) < max(min_periods, lookback + 25):
        return weights0

    equities = _safe_group(params["equity_symbols"], close.columns)
    credit = _safe_group(params["credit_symbols"], close.columns)
    defensive = _safe_group(params["defensive_symbols"], close.columns)
    stress = credit + defensive
    if len(equities) < 2 or len(stress) < 3:
        return weights0

    returns = close.pct_change()
    spy_vol = float(returns["SPY"].tail(int(params["vol_window"])).std(ddof=1) * math.sqrt(252)) if "SPY" in returns else 0.0
    if spy_vol > float(params["vol_ceiling"]):
        return weights0

    lb_ret = close.pct_change(lookback)
    equity_ret = lb_ret[equities].mean(axis=1)
    stress_ret = lb_ret[stress].mean(axis=1)
    dispersion = (equity_ret - stress_ret).dropna()
    if len(dispersion) < 25:
        return weights0
    hist = dispersion.iloc[-41:-1] if len(dispersion) >= 41 else dispersion.iloc[:-1]
    sigma = float(hist.std(ddof=1)) if len(hist) > 2 else 0.0
    if sigma <= 1e-8:
        return weights0
    z = float((dispersion.iloc[-1] - hist.mean()) / sigma)
    if abs(z) < float(params["entry_z"]) or abs(z) < float(params["exit_z"]):
        return weights0

    confirm_n = int(params["confirm_window"])
    recent = close.pct_change(confirm_n).iloc[-1]
    eq_recent = float(recent.reindex(equities).mean())
    stress_recent = float(recent.reindex(stress).mean())
    # Require at least mild stabilization in the underperforming side.
    if z < 0 and eq_recent < -0.0025:
        return weights0
    if z > 0 and stress_recent < -0.0025:
        return weights0

    vol = returns.tail(int(params["vol_window"])).std(ddof=1).replace(0.0, pd.NA) * math.sqrt(252)
    inv_vol = (float(params["target_vol"]) / vol).clip(lower=0.25, upper=2.0).fillna(1.0)
    raw = {s: 0.0 for s in symbols}
    mag = min(abs(z) / 2.5, 1.0)
    if z < 0:  # equities lagged stress proxies: buy beta, fade stress basket
        for s in equities:
            raw[s] = mag * float(inv_vol.get(s, 1.0))
        for s in stress:
            raw[s] = -mag * float(inv_vol.get(s, 1.0))
    else:  # equities ran ahead: fade beta, buy credit/defensive catch-up
        for s in equities:
            raw[s] = -mag * float(inv_vol.get(s, 1.0))
        for s in stress:
            raw[s] = mag * float(inv_vol.get(s, 1.0))

    return _normalize(raw, symbols, float(params["max_symbol_abs_weight"]))
