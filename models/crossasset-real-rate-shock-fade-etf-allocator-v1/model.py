"""AR-109 cross-asset real-rate shock-fade ETF allocator.

Research-only qfa-compatible model.  It uses only completed daily OHLCV bars
provided by qfa/Alpaca and returns target ETF weights.  The rule is fixed ex ante:
identify abrupt multi-day real-rate-proxy dislocations across duration/TIPS,
gold/USD, credit and defensive/risk sleeves, wait for 1-3 bar stabilization, then
hold a diversified long-only fade basket with SHY as residual cash.  Gross <= 1.
"""
from __future__ import annotations

import math
from typing import Any

import pandas as pd

CANDIDATE_UNIVERSE = ("TLT", "IEF", "SHY", "TIP", "GLD", "UUP", "LQD", "HYG", "SPY", "XLU")
SELECTED_UNIVERSE = CANDIDATE_UNIVERSE


class Params:
    """Tiny immutable-ish parameter container compatible with qfa's loader.

    qfa loads model files with importlib without first registering the module in
    sys.modules; stdlib dataclasses can fail under that loader on Python 3.11.
    A simple class keeps the artifact durable for native qfa smoke/backtests.
    """

    shock_lookback = 5
    stabilization_window = 2
    min_history = 90
    gross_cap = 1.0
    max_single_weight = 0.36
    shock_threshold = -0.010
    tlt_threshold = -0.014
    gld_tip_threshold = -0.020
    uup_confirmation = 0.004
    max_risk_stress = -0.040
    clv_min = 0.43
    rebound_min = -0.002
    vol_z_max = 2.85


PARAMS = Params()


def _zero(symbols: list[str]) -> dict[str, float]:
    return {s: 0.0 for s in symbols}


def _wide(prices: pd.DataFrame, symbols: list[str]) -> dict[str, pd.DataFrame] | None:
    if prices is None or len(prices) == 0:
        return None
    px = prices[prices["symbol"].isin(symbols)].copy()
    if px.empty:
        return None
    px["timestamp"] = pd.to_datetime(px["timestamp"], utc=True)
    px = px.sort_values(["timestamp", "symbol"])
    out = {}
    for col in ("open", "high", "low", "close", "volume"):
        out[col] = px.pivot(index="timestamp", columns="symbol", values=col).sort_index().ffill()
    return out


def _safe(value: Any, default: float = 0.0) -> float:
    try:
        v = float(value)
    except Exception:
        return default
    return v if math.isfinite(v) else default


def _normalize(raw: dict[str, float], symbols: list[str], gross_cap: float = PARAMS.gross_cap) -> dict[str, float]:
    w = {s: max(0.0, _safe(raw.get(s, 0.0))) for s in symbols}
    for s in list(w):
        w[s] = min(w[s], PARAMS.max_single_weight)
    gross = sum(w.values())
    if gross > gross_cap and gross > 0:
        w = {s: v / gross * gross_cap for s, v in w.items()}
    return w


def _signal_weights(wide: dict[str, pd.DataFrame], output_symbols: list[str], params: Params = PARAMS) -> dict[str, float]:
    close = wide["close"]
    high = wide["high"]
    low = wide["low"]
    volume = wide["volume"]
    required = {"TLT", "IEF", "SHY", "TIP", "GLD", "UUP", "LQD", "HYG", "SPY", "XLU"}
    if len(close) < params.min_history or not required.issubset(set(close.columns)):
        return _zero(output_symbols)

    ret3 = close.pct_change(3)
    ret5 = close.pct_change(params.shock_lookback)
    latest = close.index[-1]

    duration_shock = ((ret5.loc[latest, "TLT"] + ret5.loc[latest, "IEF"]) / 2.0) - ret5.loc[latest, "SHY"]
    tlt_shock = ret5.loc[latest, "TLT"] - ret5.loc[latest, "SHY"]
    tip_vs_tlt = ret5.loc[latest, "TIP"] - ret5.loc[latest, "TLT"]
    gld_vs_tip = ret5.loc[latest, "GLD"] - ret5.loc[latest, "TIP"]
    uup_ret = ret5.loc[latest, "UUP"]
    credit_rel = ret5.loc[latest, "HYG"] - ret5.loc[latest, "LQD"]
    defensive_rel = ret5.loc[latest, "XLU"] - ret5.loc[latest, "SPY"]

    rng = (high - low).replace(0.0, pd.NA)
    clv = ((close - low) / rng).clip(0.0, 1.0)
    vol_mean = volume.shift(1).rolling(60, min_periods=40).mean()
    vol_std = volume.shift(1).rolling(60, min_periods=40).std().replace(0.0, pd.NA)
    vol_z = ((volume - vol_mean) / vol_std).replace([float("inf"), float("-inf")], pd.NA)

    needed = [duration_shock, tlt_shock, tip_vs_tlt, gld_vs_tip, uup_ret, credit_rel, defensive_rel]
    if not all(math.isfinite(_safe(x, float("nan"))) for x in needed):
        return _zero(output_symbols)

    real_rate_shock = duration_shock <= params.shock_threshold and tlt_shock <= params.tlt_threshold
    gold_usd_dislocation = (gld_vs_tip <= params.gld_tip_threshold and uup_ret >= params.uup_confirmation)
    risk_not_crashing = ret5.loc[latest, "SPY"] > params.max_risk_stress and ret5.loc[latest, "HYG"] > params.max_risk_stress

    stab_days = close.index[-params.stabilization_window :]
    tlt_stable = bool((clv.loc[stab_days, "TLT"] >= params.clv_min).any()) and _safe(ret3.loc[latest, "TLT"]) >= params.rebound_min
    tip_stable = bool((clv.loc[stab_days, "TIP"] >= params.clv_min).any()) and _safe(ret3.loc[latest, "TIP"]) >= params.rebound_min
    gld_stable = bool((clv.loc[stab_days, "GLD"] >= params.clv_min).any()) and _safe(ret3.loc[latest, "GLD"]) >= params.rebound_min
    volume_ok = _safe(vol_z.loc[latest, "TLT"]) <= params.vol_z_max and _safe(vol_z.loc[latest, "GLD"]) <= params.vol_z_max
    stabilized = volume_ok and (tlt_stable or tip_stable or gld_stable)

    raw = {s: 0.0 for s in output_symbols}
    if (real_rate_shock or gold_usd_dislocation) and risk_not_crashing and stabilized:
        shock_strength = min(1.0, max(0.0, (-float(duration_shock) - 0.006) / 0.030))
        gold_strength = min(1.0, max(0.0, (-float(gld_vs_tip) - 0.010) / 0.055))
        credit_penalty = min(0.18, max(0.0, -float(credit_rel) * 2.0))
        gross = min(0.82, 0.42 + 0.22 * shock_strength + 0.18 * gold_strength - credit_penalty)
        duration_bucket = 0.46 + 0.10 * shock_strength
        inflation_gold_bucket = 0.30 + 0.10 * gold_strength
        defensive_bucket = max(0.08, 1.0 - duration_bucket - inflation_gold_bucket)
        sleeve = {
            "TLT": gross * duration_bucket * 0.48,
            "IEF": gross * duration_bucket * 0.34,
            "TIP": gross * (duration_bucket * 0.18 + inflation_gold_bucket * 0.45),
            "GLD": gross * inflation_gold_bucket * 0.55,
            "XLU": gross * defensive_bucket * (0.60 if defensive_rel > 0 else 0.35),
            "LQD": gross * defensive_bucket * 0.25,
            "SHY": max(0.0, 1.0 - gross),
        }
        for s, v in sleeve.items():
            if s in raw:
                raw[s] = v
    return _normalize(raw, output_symbols)


def generate_signals(context: Any) -> dict[str, float]:
    """Return target weights for qfa using completed bars in context.prices."""
    output_symbols = list(getattr(context, "symbols", []) or [])
    symbols = [s for s in output_symbols if s in SELECTED_UNIVERSE]
    wide = _wide(getattr(context, "prices", pd.DataFrame()), symbols)
    if wide is None:
        return _zero(output_symbols)
    return _signal_weights(wide, output_symbols)
