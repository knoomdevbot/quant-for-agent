"""AR-114 municipal bond ETF tax-calendar flow reversal model.

QFA contract: expose generate_signals(context) -> dict[str, float].
Uses daily OHLCV bars supplied by qfa/Alpaca. The strategy is long-only,
calendar-gated, and only allocates to municipal bond ETFs when an ex-ante
municipal tax/reinvestment window coincides with recent pressure and basic
stabilization; otherwise it uses a short Treasury/cash-like fallback if present.
"""
from __future__ import annotations

import math
from typing import Any

import pandas as pd

MUNI_CANDIDATES = ["MUB", "TFI", "SHM", "HYD", "ITM", "SUB", "PZA", "VTEB", "MLN", "HYMB", "SMB"]
CONTROL_SYMBOLS = ["SHY", "IEF", "TLT", "LQD", "HYG", "SPY"]
SELECTED_MUNIS = ["MUB", "TFI", "SHM", "HYD", "ITM", "SUB", "PZA", "VTEB"]
SELECTED_UNIVERSE = SELECTED_MUNIS + CONTROL_SYMBOLS
PARAMS = {
    "min_history": 180,
    "pressure_lookback": 21,
    "momentum_lookback": 63,
    "volume_lookback": 63,
    "vol_lookback": 21,
    "min_pressure_return": -0.012,
    "min_volume_z": -0.25,
    "max_stabilization_abs_return": 0.008,
    "max_muni_weight": 0.22,
    "gross_target": 1.0,
    "fallback_weight": 0.25,
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
    sd = _safe_float(s.std(ddof=1))
    if sd <= 1e-12:
        return 0.0
    return _safe_float((float(s.iloc[-1]) - float(s.mean())) / sd)


def _calendar_score(ts: pd.Timestamp) -> tuple[float, str]:
    """Predeclared calendar windows; no date mining/performance selection."""
    d = ts.tz_convert("UTC") if ts.tzinfo else ts.tz_localize("UTC")
    m, day = int(d.month), int(d.day)
    # Tax-loss sale pressure tends to be late Nov/Dec; buy only after pressure/stabilization.
    if (m == 11 and day >= 20) or (m == 12 and day <= 31):
        return 1.00, "late_nov_dec_tax_loss_reversal"
    # January reinvestment/coupon demand sleeve.
    if m == 1 and day <= 18:
        return 0.90, "january_reinvestment"
    # April tax-payment liquidity stress/reversal sleeve; conservative size.
    if m == 4 and 10 <= day <= 30:
        return 0.70, "april_tax_liquidity_reversal"
    # Generic month-end/turn-of-month is deliberately excluded from alpha activation.
    return 0.0, "inactive"


def _normalize(raw: dict[str, float], symbols: list[str]) -> dict[str, float]:
    out = {s: 0.0 for s in symbols}
    clean = {s: max(0.0, _safe_float(v)) for s, v in raw.items() if s in symbols and _safe_float(v) > 1e-12}
    if not clean:
        if "SHY" in symbols:
            out["SHY"] = float(PARAMS["fallback_weight"])
        return out
    capped = {s: min(v, float(PARAMS["max_muni_weight"])) for s, v in clean.items()}
    total = sum(capped.values())
    if total <= 1e-12:
        return out
    scale = min(float(PARAMS["gross_target"]), total) / total
    for s, v in capped.items():
        out[s] = v * scale
    return out


def generate_signals(context: Any) -> dict[str, float]:
    """Long municipal ETF rebound allocator around tax-calendar flow windows.

    Uses only information available as of the latest complete daily bar in
    context. Within the predeclared late-Nov/Dec, January, and April windows,
    require a negative 21-day return (pressure), at least non-collapsed volume,
    and modest latest-day stabilization. Rank candidate municipal ETFs by
    pressure intensity plus stabilization/volume support; remain mostly in SHY
    fallback outside windows or if no ETF qualifies.
    """
    symbols = list(getattr(context, "symbols", SELECTED_UNIVERSE) or SELECTED_UNIVERSE)
    prices = getattr(context, "prices", None)
    out = {s: 0.0 for s in symbols}
    if prices is None or len(prices) < 10:
        return out
    close = _pivot(prices, "close").reindex(columns=[s for s in SELECTED_UNIVERSE if s in symbols]).ffill()
    volume = _pivot(prices, "volume").reindex(columns=close.columns).ffill()
    if len(close) < int(PARAMS["min_history"]):
        if "SHY" in symbols:
            out["SHY"] = float(PARAMS["fallback_weight"])
        return out
    score, _window = _calendar_score(close.index[-1])
    if score <= 0:
        if "SHY" in symbols:
            out["SHY"] = float(PARAMS["fallback_weight"])
        return out
    ret1 = close.pct_change()
    dollar_volume = close * volume
    raw: dict[str, float] = {}
    for s in SELECTED_MUNIS:
        if s not in close or close[s].dropna().shape[0] < int(PARAMS["min_history"]):
            continue
        p21 = _safe_float(close[s].iloc[-1] / close[s].shift(int(PARAMS["pressure_lookback"])).iloc[-1] - 1.0)
        p63 = _safe_float(close[s].iloc[-1] / close[s].shift(int(PARAMS["momentum_lookback"])).iloc[-1] - 1.0)
        latest_abs = abs(_safe_float(ret1[s].iloc[-1]))
        vol_z = _z_last(dollar_volume[s], int(PARAMS["volume_lookback"]))
        rv = _safe_float(ret1[s].tail(int(PARAMS["vol_lookback"])).std(ddof=1) * math.sqrt(252.0))
        if p21 > float(PARAMS["min_pressure_return"]):
            continue
        if vol_z < float(PARAMS["min_volume_z"]):
            continue
        if latest_abs > float(PARAMS["max_stabilization_abs_return"]):
            continue
        pressure = min(2.0, abs(p21) / abs(float(PARAMS["min_pressure_return"])))
        trend_penalty = max(0.0, p63) * 8.0  # prefer rebound from pressure, not chasing rallies.
        stability = max(0.0, 1.0 - latest_abs / float(PARAMS["max_stabilization_abs_return"]))
        liq = max(0.0, min(1.5, 1.0 + 0.25 * vol_z))
        vol_penalty = max(0.5, 1.0 - max(0.0, rv - 0.10))
        raw[s] = score * max(0.0, pressure + 0.35 * stability + 0.15 * liq - trend_penalty) * vol_penalty
    return _normalize(raw, symbols)
