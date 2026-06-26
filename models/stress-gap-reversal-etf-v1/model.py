"""Stress-day overnight gap reversal detector for liquid ETFs.

QFA contract: expose generate_signals(context) -> dict[str, float].
Research-only model; it never places orders.

Intended economics: after a broad overnight risk-off shock, fade panic by
holding liquid risk ETFs long for the following qfa period. The direct research
harness evaluates same-day open-to-close and 1-3 day variants from Alpaca OHLC
bars with 5 bps per-side costs. qfa's daily close-to-close engine cannot enter
at the current open, so this model is a lagged close-to-close approximation.
"""

from __future__ import annotations

import math
import pandas as pd

UNIVERSE = ("SPY", "QQQ", "IWM", "TLT", "GLD", "XLU", "XLE")
RISK_ASSETS = ("SPY", "QQQ", "IWM", "XLE")
DEFENSIVE_ASSETS = ("TLT", "GLD", "XLU")

DEFAULT_PARAMS = {
    "gap_z_window": 60,
    "stress_z": -1.0,
    "stress_gap_bps": -50.0,
    "confirm_count": 2,
    "max_abs_weight": 0.35,
    "min_periods": 63,
}


def _zero(symbols: list[str]) -> dict[str, float]:
    return {s: 0.0 for s in symbols}


def _params(context) -> dict:
    metadata = getattr(context, "metadata", {}) or {}
    provided = metadata.get("params", {}) if isinstance(metadata, dict) else {}
    params = DEFAULT_PARAMS.copy()
    params.update({k: provided[k] for k in params.keys() & provided.keys()})
    return params


def _cap_normalize(weights: dict[str, float], cap: float) -> dict[str, float]:
    clean = {s: float(w) for s, w in weights.items() if math.isfinite(float(w))}
    gross = sum(abs(w) for w in clean.values())
    if gross <= 0.0:
        return {s: 0.0 for s in weights}
    scaled = {s: w / gross for s, w in clean.items()}
    capped = {s: max(-cap, min(cap, w)) for s, w in scaled.items()}
    capped_gross = sum(abs(w) for w in capped.values())
    if capped_gross <= 0.0:
        return {s: 0.0 for s in weights}
    return {s: float(capped.get(s, 0.0) / capped_gross) for s in weights}


def generate_signals(context):
    """Return target weights after a broad negative overnight stress gap.

    Signal definition using completed daily bars available in qfa context:
    - overnight gap = open_t / close_{t-1} - 1;
    - rolling z-score uses prior gaps only;
    - stress day if SPY gap z <= stress_z or raw gap <= stress_gap_bps and at
      least confirm_count of SPY/QQQ/IWM have negative gap z <= -0.75;
    - allocate long to SPY/QQQ/IWM/XLE inversely to trailing volatility and keep
      defensive ETFs flat. This is a lagged proxy for same-day open-to-close
      reversal because qfa cannot trade at the just-observed open.
    """
    symbols = list(getattr(context, "symbols", []) or [])
    if not symbols:
        return {}
    prices = getattr(context, "prices", pd.DataFrame()).copy()
    required = {"timestamp", "symbol", "open", "close"}
    if prices.empty or not required.issubset(prices.columns):
        return _zero(symbols)

    params = _params(context)
    use_symbols = [s for s in symbols if s in UNIVERSE]
    if len(use_symbols) < 5:
        return _zero(symbols)

    prices["timestamp"] = pd.to_datetime(prices["timestamp"], utc=True)
    px = prices[prices["symbol"].isin(use_symbols)]
    open_ = px.pivot(index="timestamp", columns="symbol", values="open").sort_index().ffill()
    close = px.pivot(index="timestamp", columns="symbol", values="close").sort_index().ffill()
    if len(close) < int(params["min_periods"]):
        return _zero(symbols)

    gap = (open_ / close.shift(1) - 1.0).replace([float("inf"), float("-inf")], pd.NA)
    window = int(params["gap_z_window"])
    gap_mean = gap.shift(1).rolling(window, min_periods=window).mean()
    gap_std = gap.shift(1).rolling(window, min_periods=window).std()
    gap_z = ((gap - gap_mean) / gap_std).replace([float("inf"), float("-inf")], pd.NA)
    latest = gap_z.index[-1]

    spy_z = gap_z.loc[latest, "SPY"] if "SPY" in gap_z.columns else pd.NA
    spy_gap = gap.loc[latest, "SPY"] if "SPY" in gap.columns else pd.NA
    confirm = 0
    for symbol in ("SPY", "QQQ", "IWM"):
        if symbol in gap_z.columns and pd.notna(gap_z.loc[latest, symbol]) and float(gap_z.loc[latest, symbol]) <= -0.75:
            confirm += 1
    stress = (
        (pd.notna(spy_z) and float(spy_z) <= float(params["stress_z"]))
        or (pd.notna(spy_gap) and float(spy_gap) <= float(params["stress_gap_bps"]) / 10000.0)
    ) and confirm >= int(params["confirm_count"])
    if not stress:
        return _zero(symbols)

    returns = close.pct_change()
    vol = returns.tail(20).std(ddof=1).replace(0.0, pd.NA)
    raw = {s: 0.0 for s in symbols}
    for symbol in RISK_ASSETS:
        if symbol in symbols and symbol in vol.index and pd.notna(vol.loc[symbol]):
            raw[symbol] = 1.0 / max(float(vol.loc[symbol]), 1e-6)
    return _cap_normalize(raw, float(params["max_abs_weight"]))
