"""AR-113 mega-cap idiosyncratic volatility normalization model.

QFA contract: expose generate_signals(context) -> dict[str, float].
Uses only daily OHLCV bars supplied by qfa/Alpaca. The model fades
single-name residual stress/range expansion events that did not achieve
same-day close-location follow-through, with SPY and mapped sector ETF
context removed and a small SPY/sector residual hedge approximation.
"""
from __future__ import annotations

import math
from typing import Any

import pandas as pd

EQUITY_CANDIDATES = [
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "AVGO", "TSLA", "JPM", "LLY",
    "XOM", "UNH", "HD", "COST", "PG", "MA", "V", "JNJ", "ABBV", "NFLX", "AMD", "CRM",
    "ORCL", "KO", "PEP",
]
SELECTED_EQUITIES = [
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "AVGO", "TSLA", "JPM", "LLY",
    "XOM", "UNH", "COST", "MA", "V", "JNJ", "NFLX", "AMD", "CRM", "ORCL", "KO",
]
SECTOR_ETFS = ["XLK", "XLY", "XLC", "XLF", "XLV", "XLE", "XLP", "XLI", "XLU"]
SELECTED_UNIVERSE = SELECTED_EQUITIES + ["SPY"] + SECTOR_ETFS
SECTOR_MAP = {
    "AAPL": "XLK", "MSFT": "XLK", "NVDA": "XLK", "AVGO": "XLK", "AMD": "XLK", "CRM": "XLK", "ORCL": "XLK",
    "AMZN": "XLY", "TSLA": "XLY", "HD": "XLY", "COST": "XLP",
    "META": "XLC", "GOOGL": "XLC", "NFLX": "XLC",
    "JPM": "XLF", "MA": "XLF", "V": "XLF",
    "LLY": "XLV", "UNH": "XLV", "JNJ": "XLV", "ABBV": "XLV",
    "XOM": "XLE", "PG": "XLP", "KO": "XLP", "PEP": "XLP",
}
PARAMS = {
    "min_history": 160,
    "beta_lookback": 126,
    "range_lookback": 40,
    "resid_z_lookback": 126,
    "volume_lookback": 60,
    "range_z_threshold": 1.10,
    "resid_abs_z_threshold": 1.00,
    "min_abs_resid_return": 0.006,
    "failed_followthrough_clv": 0.62,
    "volume_z_min": -0.25,
    "max_names": 6,
    "single_name_cap": 0.20,
    "sector_cap": 0.40,
    "gross_equity_target": 0.90,
    "hedge_fraction": 0.35,
}


def _pivot(prices: pd.DataFrame, field: str) -> pd.DataFrame:
    px = prices.copy()
    px["timestamp"] = pd.to_datetime(px["timestamp"], utc=True)
    return px.pivot(index="timestamp", columns="symbol", values=field).sort_index().ffill()


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return default
    return out if math.isfinite(out) else default


def _z_last(series: pd.Series, lookback: int) -> float:
    s = series.dropna().tail(lookback)
    if len(s) < max(20, lookback // 2):
        return 0.0
    sd = float(s.std(ddof=1))
    if not math.isfinite(sd) or sd <= 1e-12:
        return 0.0
    return _safe_float((float(s.iloc[-1]) - float(s.mean())) / sd)


def _rolling_residual(stock: pd.Series, spy: pd.Series, sector: pd.Series, lookback: int) -> pd.Series:
    df = pd.concat([stock, spy, sector], axis=1).dropna()
    if len(df) < max(40, lookback // 2):
        return stock * 0.0
    df = df.tail(lookback)
    y = df.iloc[:, 0]
    x1 = df.iloc[:, 1]
    x2 = df.iloc[:, 2]
    # Lightweight two-factor beta approximation via covariance; robust enough for online signal generation.
    b1 = _safe_float(y.cov(x1) / max(_safe_float(x1.var()), 1e-10))
    rem = y - b1 * x1
    b2 = _safe_float(rem.cov(x2) / max(_safe_float(x2.var()), 1e-10))
    aligned = pd.concat([stock, spy, sector], axis=1).dropna()
    return aligned.iloc[:, 0] - b1 * aligned.iloc[:, 1] - b2 * aligned.iloc[:, 2]


def _normalize_with_caps(raw: dict[str, float], symbols: list[str]) -> dict[str, float]:
    p = PARAMS
    clean = {s: _safe_float(v) for s, v in raw.items() if abs(_safe_float(v)) > 1e-12}
    if not clean:
        return {s: 0.0 for s in symbols}
    # Iteratively cap single names and sector totals before gross normalization.
    for _ in range(5):
        gross = sum(abs(v) for v in clean.values())
        if gross <= 1e-12:
            return {s: 0.0 for s in symbols}
        weights = {s: v / gross * float(p["gross_equity_target"]) for s, v in clean.items()}
        changed = False
        for s, w in list(weights.items()):
            if s in SELECTED_EQUITIES and abs(w) > float(p["single_name_cap"]):
                clean[s] *= float(p["single_name_cap"]) / abs(w)
                changed = True
        for etf in SECTOR_ETFS:
            names = [s for s in weights if SECTOR_MAP.get(s) == etf]
            sec_abs = sum(abs(weights[s]) for s in names)
            if sec_abs > float(p["sector_cap"]):
                scale = float(p["sector_cap"]) / sec_abs
                for s in names:
                    clean[s] *= scale
                changed = True
        if not changed:
            out = {s: 0.0 for s in symbols}
            out.update(weights)
            return out
    gross = sum(abs(v) for v in clean.values())
    out = {s: 0.0 for s in symbols}
    if gross > 1e-12:
        out.update({s: v / gross * float(p["gross_equity_target"]) for s, v in clean.items()})
    return out


def generate_signals(context: Any) -> dict[str, float]:
    """Fade idiosyncratic failed residual range/volatility expansion in mega-caps.

    Event is measured on the latest complete bar in context. For each stock,
    compute residual return versus SPY and mapped sector ETF, require elevated
    intraday range and absolute residual stress, require poor close-location
    follow-through in the direction of the residual move, then take the opposite
    exposure. A partial SPY and sector ETF hedge offsets aggregate residual beta.
    """
    symbols = list(getattr(context, "symbols", SELECTED_UNIVERSE) or SELECTED_UNIVERSE)
    prices = getattr(context, "prices", None)
    out = {s: 0.0 for s in symbols}
    if prices is None or len(prices) < 10:
        return out
    close = _pivot(prices, "close").reindex(columns=[s for s in SELECTED_UNIVERSE if s in symbols]).ffill()
    high = _pivot(prices, "high").reindex(columns=close.columns).ffill()
    low = _pivot(prices, "low").reindex(columns=close.columns).ffill()
    volume = _pivot(prices, "volume").reindex(columns=close.columns).ffill()
    if "SPY" not in close or len(close.dropna(how="all")) < int(PARAMS["min_history"]):
        return out
    ret = close.pct_change()
    tr = (high - low) / close.shift(1)
    dollar_volume = close * volume
    raw: dict[str, float] = {}
    for s in SELECTED_EQUITIES:
        sec = SECTOR_MAP.get(s)
        if s not in close or sec not in close:
            continue
        if min(close[s].dropna().shape[0], close[sec].dropna().shape[0]) < int(PARAMS["min_history"]):
            continue
        resid = _rolling_residual(ret[s], ret["SPY"], ret[sec], int(PARAMS["beta_lookback"]))
        if len(resid.dropna()) < 60:
            continue
        resid_ret = _safe_float(resid.iloc[-1])
        direction = 1 if resid_ret > 0 else -1
        if abs(resid_ret) < float(PARAMS["min_abs_resid_return"]):
            continue
        range_z = _z_last(tr[s], int(PARAMS["range_lookback"]))
        resid_abs_z = _z_last(resid.abs(), int(PARAMS["resid_z_lookback"]))
        vol_z = _z_last(dollar_volume[s], int(PARAMS["volume_lookback"]))
        if range_z < float(PARAMS["range_z_threshold"]) or resid_abs_z < float(PARAMS["resid_abs_z_threshold"]):
            continue
        if vol_z < float(PARAMS["volume_z_min"]):
            continue
        clv = _safe_float((close[s].iloc[-1] - low[s].iloc[-1]) / max(high[s].iloc[-1] - low[s].iloc[-1], 1e-9), 0.5)
        # Failed follow-through: positive residual that cannot close near high, or negative residual that cannot close near low.
        if direction > 0 and clv > float(PARAMS["failed_followthrough_clv"]):
            continue
        if direction < 0 and clv < 1.0 - float(PARAMS["failed_followthrough_clv"]):
            continue
        strength = (range_z - float(PARAMS["range_z_threshold"])) + 0.75 * (resid_abs_z - float(PARAMS["resid_abs_z_threshold"])) + 0.15 * max(0.0, vol_z)
        raw[s] = -direction * max(0.0, strength)
    if not raw:
        return out
    raw = dict(sorted(raw.items(), key=lambda kv: abs(kv[1]), reverse=True)[: int(PARAMS["max_names"])])
    # Partial residual basket hedge using mapped sectors and SPY only when qfa context includes them.
    if "SPY" in symbols:
        net = sum(raw.values())
        raw["SPY"] = raw.get("SPY", 0.0) - float(PARAMS["hedge_fraction"]) * net
    for sec in SECTOR_ETFS:
        if sec in symbols:
            sec_net = sum(v for k, v in raw.items() if SECTOR_MAP.get(k) == sec)
            if abs(sec_net) > 1e-12:
                raw[sec] = raw.get(sec, 0.0) - 0.5 * float(PARAMS["hedge_fraction"]) * sec_net
    return _normalize_with_caps(raw, symbols)
