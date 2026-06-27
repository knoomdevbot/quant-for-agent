"""AR-121 ETF family-relative OHLCV liquidity-pressure allocator.

Research-only qfa alpha model.  Uses only daily OHLCV fields available in the
AlphaContext; no external files, CSV data, daemon state, or order side effects.
The signal shorts ETF/family names showing positive end-of-day liquidity-pressure
proxies and buys peers with negative pressure, expecting 1-5 day mean reversion.
"""
from __future__ import annotations

import math
from statistics import median

import pandas as pd

FAMILIES = {
    "broad_equity": ("SPY", "QQQ", "DIA", "IWM", "VTI", "RSP"),
    "sectors": ("XLK", "XLY", "XLP", "XLV", "XLF", "XLI", "XLE", "XLU", "XLB", "XLRE", "XLC"),
    "style_factor": ("IWF", "IWD", "IWO", "IWN", "MTUM", "QUAL", "VLUE", "USMV", "SPLV"),
    "international": ("EFA", "EEM", "VEA", "VWO", "EWJ", "EWU", "EWG", "FXI"),
    "rates_credit": ("SHY", "IEF", "TLT", "TIP", "LQD", "HYG", "JNK", "BND", "AGG", "MUB"),
    "commodities_real": ("GLD", "SLV", "DBC", "USO", "UNG", "XOP", "GDX", "VNQ"),
}
SYMBOL_TO_FAMILY = {s: fam for fam, names in FAMILIES.items() for s in names}
MIN_HISTORY = 130
Z_LOOKBACK = 60
VOL_LOOKBACK = 20
TOP_BOTTOM_N = 6
MAX_ABS_WEIGHT = 0.125
MIN_SIGNAL = 0.35


def _finite(x: float, default: float = 0.0) -> float:
    try:
        y = float(x)
    except Exception:
        return default
    return y if math.isfinite(y) else default


def _z_last(series: pd.Series, lookback: int = Z_LOOKBACK) -> float:
    s = pd.to_numeric(series, errors="coerce").dropna().tail(lookback + 1)
    if len(s) < max(20, lookback // 2):
        return 0.0
    last = float(s.iloc[-1])
    hist = s.iloc[:-1]
    sd = float(hist.std(ddof=0))
    if not math.isfinite(sd) or sd <= 1e-12:
        return 0.0
    return max(-4.0, min(4.0, (last - float(hist.mean())) / sd))


def _clip(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def generate_signals(context) -> dict[str, float]:
    symbols = list(context.symbols)
    if context.prices is None or context.prices.empty:
        return {s: 0.0 for s in symbols}

    p = context.prices.copy()
    p["timestamp"] = pd.to_datetime(p["timestamp"], utc=True)
    p = p[p["symbol"].isin(symbols)].sort_values(["timestamp", "symbol"])
    close = p.pivot(index="timestamp", columns="symbol", values="close").ffill()
    open_ = p.pivot(index="timestamp", columns="symbol", values="open").ffill()
    high = p.pivot(index="timestamp", columns="symbol", values="high").ffill()
    low = p.pivot(index="timestamp", columns="symbol", values="low").ffill()
    volume = p.pivot(index="timestamp", columns="symbol", values="volume").ffill()
    if len(close) < MIN_HISTORY:
        return {s: 0.0 for s in symbols}

    raw = {}
    for s in symbols:
        if s not in close.columns or s not in SYMBOL_TO_FAMILY:
            continue
        c = close[s].dropna()
        if len(c) < MIN_HISTORY:
            continue
        o = open_[s].reindex(c.index).ffill()
        h = high[s].reindex(c.index).ffill()
        lo_px = low[s].reindex(c.index).ffill()
        v = volume[s].reindex(c.index).ffill()
        prev_c = c.shift(1)
        ret1 = c.pct_change()
        gap = o / prev_c - 1.0
        intraday = c / o - 1.0
        rng = (h - lo_px) / prev_c
        denom = (h - lo_px).replace(0.0, float("nan"))
        close_loc = ((c - lo_px) / denom - 0.5).fillna(0.0)
        dollar_vol = (c * v).where((c > 0) & (v > 0))
        vol_z = _z_last(dollar_vol.apply(math.log))
        range_z = _z_last(rng)
        ret_z = _z_last(ret1)
        gap_resid = _finite((gap - intraday.rolling(5).mean()).iloc[-1])
        latest_ret = _finite(ret1.iloc[-1])
        latest_clv = _finite(close_loc.iloc[-1])
        rv_disloc = _clip(ret_z * max(0.0, vol_z), -4.0, 4.0)
        pressure = (
            0.30 * _clip(vol_z, -3.0, 3.0) * (1.0 if latest_ret >= 0 else -1.0)
            + 0.24 * _clip(latest_clv * 2.0, -1.0, 1.0)
            + 0.18 * _clip(gap_resid / 0.015, -2.0, 2.0)
            + 0.16 * _clip(range_z, -3.0, 3.0) * (1.0 if latest_ret >= 0 else -1.0)
            + 0.12 * rv_disloc
        )
        # Temper very high realized volatility ETFs, but do not performance-select.
        vol20 = _finite(ret1.tail(VOL_LOOKBACK).std(ddof=0) * math.sqrt(252.0))
        raw[s] = pressure / max(1.0, vol20 / 0.30)

    by_family = {}
    for s, value in raw.items():
        by_family.setdefault(SYMBOL_TO_FAMILY[s], []).append(value)
    fam_med = {fam: median(vals) for fam, vals in by_family.items() if vals}
    rel = {s: raw[s] - fam_med.get(SYMBOL_TO_FAMILY[s], 0.0) for s in raw}
    eligible = {s: v for s, v in rel.items() if abs(v) >= MIN_SIGNAL}
    if len(eligible) < 4:
        return {s: 0.0 for s in symbols}

    longs = sorted(eligible, key=lambda s: eligible[s])[:TOP_BOTTOM_N]
    shorts = sorted(eligible, key=lambda s: eligible[s], reverse=True)[:TOP_BOTTOM_N]
    weights = {s: 0.0 for s in symbols}
    if longs:
        for s in longs:
            weights[s] = min(MAX_ABS_WEIGHT, 0.5 / len(longs))
    if shorts:
        for s in shorts:
            weights[s] = -min(MAX_ABS_WEIGHT, 0.5 / len(shorts))
    gross = sum(abs(w) for w in weights.values())
    return {s: (w / gross if gross > 1.0 else w) for s, w in weights.items()}
