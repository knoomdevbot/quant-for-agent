"""AR-132 sponsor/exposure ETF residual-dispersion convergence model.

QFA contract: expose generate_signals(context) -> dict[symbol, weight].
Uses only lagged daily OHLCV close-derived returns supplied by qfa/Alpaca. The
sponsor label is used only for fixed ex-ante cluster construction; it is not a
claim about creations/redemptions, flows, or sponsor behavior. No orders.
"""
from __future__ import annotations

import math

import pandas as pd

# Fixed candidate/selected universe is documented in config/metadata.  The model
# trades only symbols present in context.symbols and context.prices.
UNIVERSE = [
    "SPY", "SPLG", "SPYG", "SPYV", "MDY", "SPMD", "SLY", "SPSM",
    "IVV", "IWB", "IVE", "IVW", "IUSV", "IUSG", "IJH", "IWR", "IJR", "IWM",
    "VOO", "VTI", "VV", "VTV", "VUG", "VO", "VOE", "VOT", "VB", "VBR", "VBK",
]

CLUSTERS = {
    "spdr_large_core": ["SPY", "SPLG"],
    "spdr_large_style": ["SPYG", "SPYV"],
    "spdr_mid_core": ["MDY", "SPMD"],
    "spdr_small_core": ["SLY", "SPSM"],
    "ishares_large_core": ["IVV", "IWB"],
    "ishares_large_style": ["IVE", "IVW", "IUSV", "IUSG"],
    "ishares_mid_core": ["IJH", "IWR"],
    "ishares_small_core": ["IJR", "IWM"],
    "vanguard_large_core": ["VOO", "VTI", "VV"],
    "vanguard_large_style": ["VTV", "VUG"],
    "vanguard_mid_style": ["VO", "VOE", "VOT"],
    "vanguard_small_style": ["VB", "VBR", "VBK"],
}

EXPOSURE_PROXY = {
    "large_core": "SPY",
    "large_style": "SPY",
    "mid_core": "IJH",
    "mid_style": "IJH",
    "small_core": "IWM",
    "small_style": "IWM",
}

PARAMS = {
    "beta_window": 126,
    "residual_lookback": 3,
    "dispersion_window": 126,
    "stress_window": 20,
    "min_history": 275,
    "dispersion_z_entry": 1.0,
    "residual_z_entry": 0.65,
    "stress_return_threshold": -0.012,
    "stress_vol_z_threshold": 0.35,
    "max_gross": 1.0,
    "symbol_cap": 0.18,
    "cluster_cap": 0.34,
}


def _zero(symbols: list[str]) -> dict[str, float]:
    return {s: 0.0 for s in symbols}


def _safe_std(x: pd.Series) -> float:
    y = x.dropna()
    if len(y) < 2:
        return float("nan")
    v = float(y.std(ddof=1))
    return v if math.isfinite(v) and v > 0 else float("nan")


def _close_matrix(context) -> pd.DataFrame:
    prices = getattr(context, "prices", None)
    symbols = list(getattr(context, "symbols", []) or [])
    if prices is None or prices.empty or not {"timestamp", "symbol", "close"}.issubset(prices.columns):
        return pd.DataFrame()
    allowed = [s for s in UNIVERSE if s in symbols]
    p = prices[prices["symbol"].isin(allowed)].copy()
    if p.empty:
        return pd.DataFrame()
    p["timestamp"] = pd.to_datetime(p["timestamp"], utc=True)
    return p.pivot(index="timestamp", columns="symbol", values="close").sort_index().ffill().dropna(axis=1, how="all")


def _cluster_exposure(cluster_name: str) -> str:
    for suffix in ("large_core", "large_style", "mid_core", "mid_style", "small_core", "small_style"):
        if cluster_name.endswith(suffix):
            return suffix
    return "large_core"


def _cap_normalize(raw: dict[str, float], cluster_for_symbol: dict[str, str], symbols: list[str]) -> dict[str, float]:
    capped = {s: max(-PARAMS["symbol_cap"], min(PARAMS["symbol_cap"], float(raw.get(s, 0.0)))) for s in symbols}
    for cluster in set(cluster_for_symbol.values()):
        members = [s for s, c in cluster_for_symbol.items() if c == cluster]
        gross = sum(abs(capped.get(s, 0.0)) for s in members)
        if gross > PARAMS["cluster_cap"]:
            scale = PARAMS["cluster_cap"] / gross
            for s in members:
                capped[s] *= scale
    gross = sum(abs(v) for v in capped.values())
    if gross <= 0:
        return _zero(symbols)
    scale = min(1.0, PARAMS["max_gross"] / gross)
    return {s: float(capped[s] * scale) for s in symbols}


def generate_signals(context) -> dict[str, float]:
    """Return target weights for the next daily bar; all features use completed bars only."""
    symbols = list(getattr(context, "symbols", []) or [])
    if not symbols:
        return {}
    close = _close_matrix(context)
    if close.empty or len(close) < PARAMS["min_history"]:
        return _zero(symbols)
    ret = close.pct_change().dropna(how="all")
    if len(ret) < PARAMS["min_history"] - 1:
        return _zero(symbols)

    raw = {s: 0.0 for s in symbols}
    cluster_for_symbol: dict[str, str] = {}
    p = PARAMS

    for cluster_name, members0 in CLUSTERS.items():
        members = [s for s in members0 if s in ret.columns and s in symbols]
        exposure = _cluster_exposure(cluster_name)
        proxy = EXPOSURE_PROXY.get(exposure, "SPY")
        if proxy not in ret.columns or len(members) < 2:
            continue

        proxy_ret = ret[proxy].dropna()
        # Stress gate uses only the exposure proxy's completed trailing returns/volatility.
        trailing_proxy = proxy_ret.iloc[-max(p["stress_window"], p["dispersion_window"]):]
        if len(trailing_proxy) < p["dispersion_window"]:
            continue
        stress_return = float(proxy_ret.iloc[-p["residual_lookback"]:].sum())
        vol20 = proxy_ret.rolling(p["stress_window"]).std(ddof=1).dropna()
        if len(vol20) < p["dispersion_window"]:
            continue
        vwin = vol20.iloc[-p["dispersion_window"]:]
        vsd = _safe_std(vwin)
        vol_z = (float(vol20.iloc[-1]) - float(vwin.mean())) / vsd if math.isfinite(vsd) else 0.0
        if not (stress_return <= p["stress_return_threshold"] or vol_z >= p["stress_vol_z_threshold"]):
            continue

        residual_rolls = {}
        residual_scores = {}
        for sym in members:
            pair = pd.concat([ret[sym], ret[proxy]], axis=1).dropna()
            if len(pair) < p["min_history"]:
                continue
            y = pair.iloc[:, 0]
            x = pair.iloc[:, 1]
            xb = x.iloc[-p["beta_window"]:]
            yb = y.iloc[-p["beta_window"]:]
            var = xb.var(ddof=1)
            beta = float(yb.cov(xb) / var) if var and math.isfinite(float(var)) else 1.0
            beta = max(0.2, min(1.8, beta))
            resid = y - beta * x
            roll = resid.rolling(p["residual_lookback"]).sum().dropna()
            if len(roll) < p["dispersion_window"]:
                continue
            rvol = _safe_std(resid.iloc[-p["beta_window"]:])
            if not math.isfinite(rvol):
                continue
            residual_rolls[sym] = roll
            residual_scores[sym] = float(roll.iloc[-1]) / (rvol * math.sqrt(p["residual_lookback"]))

        if len(residual_scores) < 2:
            continue
        hist = pd.concat(residual_rolls, axis=1).dropna()
        if len(hist) < p["dispersion_window"]:
            continue
        disp = hist.std(axis=1, ddof=1).dropna()
        dwin = disp.iloc[-p["dispersion_window"]:]
        dsd = _safe_std(dwin)
        if not math.isfinite(dsd):
            continue
        dispersion_z = (float(disp.iloc[-1]) - float(dwin.mean())) / dsd
        if dispersion_z < p["dispersion_z_entry"]:
            continue

        vals = pd.Series(residual_scores).dropna()
        csd = _safe_std(vals)
        if not math.isfinite(csd):
            continue
        center = float(vals.mean())
        scores = {s: -((float(v) - center) / csd) for s, v in vals.items()}
        scores = {s: v for s, v in scores.items() if abs(v) >= p["residual_z_entry"]}
        gross = sum(abs(v) for v in scores.values())
        if gross <= 0:
            continue
        for s, score in scores.items():
            raw[s] += score / gross / max(1, len(CLUSTERS) // 3)
            cluster_for_symbol[s] = cluster_name

    if sum(abs(v) for v in raw.values()) <= 0:
        return _zero(symbols)
    return _cap_normalize(raw, cluster_for_symbol, symbols)
