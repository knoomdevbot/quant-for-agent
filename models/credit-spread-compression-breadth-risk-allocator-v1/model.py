"""AR-102 credit-spread compression breadth risk allocator.

Research-only qfa alpha contract: expose generate_signals(context) -> dict[str, float].
Uses only historical daily OHLCV bars supplied by qfa/Alpaca. Credit ETF price
ratios are used as tradeable spread-proxy state variables; no OAS, CSV, daemon,
or order path is required.
"""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

UNIVERSE = [
    "HYG", "JNK", "LQD", "VCIT", "TIP", "TLT", "IEF", "SHY",
    "SPY", "QQQ", "IWM", "XLF", "XLI", "XLE", "XLU", "XLP", "XLV", "GLD",
]
CREDIT_RISK = ["HYG", "JNK", "VCIT"]
QUALITY_DURATION = ["LQD", "IEF", "TLT", "TIP"]
RISK_ASSETS = ["SPY", "QQQ", "IWM", "XLF", "XLI", "XLE"]
DEFENSIVE = ["IEF", "TLT", "GLD", "XLU", "XLP", "XLV", "SHY"]
PARAMS = {
    "fast": 20,
    "mid": 60,
    "slow": 126,
    "z_window": 126,
    "vol_window": 20,
    "compression_breadth_threshold": 0.60,
    "expansion_breadth_threshold": 0.40,
    "z_threshold": 0.35,
    "max_weight": 0.35,
}


def _pivot(prices: pd.DataFrame, field: str = "close") -> pd.DataFrame:
    px = prices.copy()
    px["timestamp"] = pd.to_datetime(px["timestamp"], utc=True)
    return px.pivot(index="timestamp", columns="symbol", values=field).sort_index().ffill()


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return default
    return out if math.isfinite(out) else default


def _ret(close: pd.DataFrame, symbol: str, lookback: int) -> float:
    if symbol not in close:
        return 0.0
    s = close[symbol].dropna()
    if len(s) <= lookback:
        return 0.0
    return _safe_float(s.iloc[-1] / s.iloc[-1 - lookback] - 1.0)


def _ratio_z(close: pd.DataFrame, numerator: str, denominator: str, window: int) -> float:
    if numerator not in close or denominator not in close:
        return 0.0
    ratio = (close[numerator] / close[denominator]).dropna()
    if len(ratio) < window + 2:
        return 0.0
    lr = ratio.apply(math.log).diff().rolling(20).sum().dropna()
    hist = lr.tail(window)
    if len(hist) < 40:
        return 0.0
    sd = _safe_float(hist.std(ddof=1), 0.0)
    if sd <= 1e-12:
        return 0.0
    return _safe_float((hist.iloc[-1] - hist.mean()) / sd)


def _cap_normalize(raw: dict[str, float], symbols: list[str], cap: float) -> dict[str, float]:
    clean = {s: max(0.0, _safe_float(raw.get(s, 0.0))) for s in symbols}
    total = sum(clean.values())
    if total <= 0.0:
        return {s: 0.0 for s in symbols}
    weights = {s: v / total for s, v in clean.items()}
    for _ in range(12):
        excess = sum(max(0.0, v - cap) for v in weights.values())
        weights = {s: min(v, cap) for s, v in weights.items()}
        room = {s: cap - v for s, v in weights.items() if v < cap - 1e-12}
        room_total = sum(room.values())
        if excess <= 1e-12 or room_total <= 0.0:
            break
        for s, room_s in room.items():
            weights[s] += excess * room_s / room_total
    gross = sum(weights.values())
    if gross > 0:
        weights = {s: v / gross for s, v in weights.items()}
    return {s: float(weights.get(s, 0.0)) for s in symbols}


def generate_signals(context: Any) -> dict[str, float]:
    """Return long-only ETF target weights from credit compression breadth.

    Compression is inferred from positive HYG/LQD and HYG/IEF ratio momentum plus
    breadth among high-yield/intermediate-credit ETFs. Expansion or duration
    shock regimes rotate to duration, gold, defensive sectors and SHY fallback.
    """
    symbols = list(getattr(context, "symbols", UNIVERSE) or UNIVERSE)
    out = {s: 0.0 for s in symbols}
    prices = getattr(context, "prices", None)
    if prices is None or len(prices) < 160:
        return out

    close = _pivot(prices, "close").reindex(columns=[s for s in symbols if s in UNIVERSE]).ffill()
    if close.empty or len(close.dropna(how="all")) < 150:
        return out
    available = [s for s in close.columns if close[s].dropna().shape[0] >= 140]
    if "HYG" not in available or "LQD" not in available or "IEF" not in available:
        return out

    p = PARAMS.copy()
    r_hyg_lqd_20 = _ret(close.assign(_R=close["HYG"] / close["LQD"]), "_R", int(p["fast"]))
    r_hyg_ief_20 = _ret(close.assign(_R=close["HYG"] / close["IEF"]), "_R", int(p["fast"]))
    z_hyg_lqd = _ratio_z(close, "HYG", "LQD", int(p["z_window"]))
    z_hyg_ief = _ratio_z(close, "HYG", "IEF", int(p["z_window"]))

    credit_candidates = [s for s in CREDIT_RISK + ["LQD"] if s in available]
    credit_breadth = sum(_ret(close, s, int(p["fast"])) > _ret(close, "IEF", int(p["fast"])) for s in credit_candidates) / max(1, len(credit_candidates))
    risk_breadth = sum(_ret(close, s, int(p["mid"])) > 0.0 for s in [x for x in RISK_ASSETS if x in available]) / max(1, len([x for x in RISK_ASSETS if x in available]))
    spy_slow = _ret(close, "SPY", int(p["slow"])) if "SPY" in available else 0.0

    rets = close[available].pct_change().tail(int(p["vol_window"]))
    rv = rets.std(ddof=1) * math.sqrt(252) if len(rets) > 2 else pd.Series(dtype=float)
    def inv_vol(s: str, floor: float = 0.05) -> float:
        return 1.0 / max(_safe_float(rv.get(s), 0.18), floor)

    compression_score = 0.45 * z_hyg_lqd + 0.35 * z_hyg_ief + 8.0 * (r_hyg_lqd_20 + r_hyg_ief_20) + 0.50 * (credit_breadth - 0.5)
    raw: dict[str, float] = {}

    if compression_score > float(p["z_threshold"]) and credit_breadth >= float(p["compression_breadth_threshold"]) and spy_slow > -0.08:
        for s in [x for x in CREDIT_RISK if x in available]:
            raw[s] = (0.22 + max(0.0, _ret(close, s, int(p["mid"])))) * inv_vol(s)
        for s in [x for x in RISK_ASSETS if x in available and _ret(close, x, int(p["mid"])) > -0.03]:
            raw[s] = (0.08 + max(0.0, _ret(close, s, int(p["mid"])))) * inv_vol(s)
        if "LQD" in available:
            raw["LQD"] = 0.08 * inv_vol("LQD", 0.03)
    elif compression_score < -float(p["z_threshold"]) or credit_breadth <= float(p["expansion_breadth_threshold"]) or spy_slow < -0.10:
        for s in [x for x in ["IEF", "TLT", "GLD", "XLU", "XLP", "XLV"] if x in available]:
            raw[s] = (0.16 + max(0.0, _ret(close, s, int(p["fast"])))) * inv_vol(s, 0.03)
        if "SHY" in available:
            raw["SHY"] = 0.40
    else:
        # Neutral credit state: quality credit / cash-like ballast with limited equity confirmation.
        for s in [x for x in ["LQD", "VCIT", "IEF", "SHY", "GLD"] if x in available]:
            raw[s] = 0.15 * inv_vol(s, 0.025)
        if risk_breadth > 0.55:
            for s in [x for x in ["SPY", "XLP", "XLV"] if x in available]:
                raw[s] = 0.05 * inv_vol(s)

    return _cap_normalize(raw, symbols, float(p["max_weight"]))
