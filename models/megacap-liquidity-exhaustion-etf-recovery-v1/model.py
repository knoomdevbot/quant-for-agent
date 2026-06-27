"""AR-119 mega-cap liquidity-exhaustion recovery breadth ETF allocator.

QFA-compatible model using only daily OHLCV bars in ``context.prices``.  It
measures capitulation/recovery breadth across a fixed ex-ante liquid US
mega-cap equity universe, then expresses the signal only through diversified
ETF sleeves or cash.  No external files, state, or intraday data are used.
"""

from __future__ import annotations

import math
from typing import Dict, Iterable

import pandas as pd

SIGNAL_UNIVERSE = (
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "GOOG", "AVGO", "TSLA", "BRK.B",
    "JPM", "LLY", "V", "UNH", "XOM", "MA", "COST", "WMT", "PG", "JNJ",
    "HD", "ABBV", "BAC", "KO", "NFLX", "ORCL", "MRK", "CVX", "CRM", "AMD",
    "PEP", "ADBE", "TMO", "LIN", "MCD", "CSCO", "ABT", "ACN", "WFC", "GE",
    "QCOM", "TXN", "IBM", "INTU", "AMAT", "CAT", "NOW", "VZ", "DHR", "DIS",
    "PFE", "PM", "ISRG", "NEE", "RTX", "SPGI", "UBER", "GS", "LOW", "HON",
)

TRADE_UNIVERSE = (
    "SPY", "QQQ", "IWM", "DIA", "XLK", "XLF", "XLE", "XLV", "XLY", "XLI",
    "XLP", "XLU", "XLB", "XLRE", "TLT", "IEF", "SHY", "GLD", "USMV", "QUAL",
)
RISK_ETFS = ("SPY", "QQQ", "IWM", "DIA", "XLK", "XLF", "XLV", "XLY", "XLI", "USMV", "QUAL")
DEFENSIVE_ETFS = ("SHY", "IEF", "TLT", "GLD", "XLP", "XLU", "XLV", "USMV")
SECTOR_MAP = {
    "XLK": ("AAPL", "MSFT", "NVDA", "AVGO", "ORCL", "CRM", "AMD", "ADBE", "CSCO", "QCOM", "TXN", "IBM", "INTU", "AMAT", "NOW"),
    "XLF": ("JPM", "V", "MA", "BAC", "WFC", "GS", "BRK.B"),
    "XLE": ("XOM", "CVX"),
    "XLV": ("LLY", "UNH", "JNJ", "ABBV", "MRK", "TMO", "ABT", "DHR", "PFE", "ISRG"),
    "XLY": ("AMZN", "TSLA", "HD", "NFLX", "MCD", "DIS", "LOW", "UBER"),
    "XLP": ("COST", "WMT", "PG", "KO", "PEP", "PM"),
    "XLI": ("GE", "CAT", "RTX", "HON", "ACN"),
    "XLU": ("NEE",),
}

MIN_HISTORY = 155
BASELINE_WINDOW = 120
RECOVERY_WINDOW = 3
TREND_WINDOW = 63
VOL_WINDOW = 42
MAX_SINGLE_WEIGHT = 0.30
MAX_GROSS = 0.95
MIN_ACTIVATION = 0.12


def _safe_float(value, default: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return default
    return out if math.isfinite(out) else default


def _clip(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _zscore(current: float, history: pd.Series) -> float:
    hist = history.replace([math.inf, -math.inf], pd.NA).dropna()
    if len(hist) < 40:
        return 0.0
    sd = _safe_float(hist.std(ddof=1))
    if sd <= 1e-12:
        return 0.0
    return _clip((current - _safe_float(hist.mean())) / sd, -4.0, 4.0)


def _last_return(close: pd.DataFrame, symbol: str, window: int) -> float:
    if symbol not in close.columns:
        return 0.0
    s = close[symbol].dropna()
    if len(s) <= window or s.iloc[-window - 1] <= 0:
        return 0.0
    return _safe_float(s.iloc[-1] / s.iloc[-window - 1] - 1.0)


def _realized_vol(close: pd.DataFrame, symbol: str, window: int = VOL_WINDOW) -> float:
    if symbol not in close.columns:
        return 0.0
    r = close[symbol].dropna().pct_change().dropna().tail(window)
    if len(r) < 15:
        return 0.0
    return _safe_float(r.std(ddof=1) * math.sqrt(252.0))


def _mean(values: Iterable[float]) -> float:
    vals = [v for v in values if math.isfinite(v)]
    return sum(vals) / len(vals) if vals else 0.0


def _normalize_capped(scores: Dict[str, float], budget: float) -> Dict[str, float]:
    positives = {k: max(0.0, _safe_float(v)) for k, v in scores.items()}
    total = sum(positives.values())
    if budget <= 0.0 or total <= 0.0:
        return {k: 0.0 for k in scores}
    weights = {k: budget * v / total for k, v in positives.items()}
    for _ in range(8):
        excess = sum(max(0.0, w - MAX_SINGLE_WEIGHT) for w in weights.values())
        if excess <= 1e-12:
            break
        capped = {k for k, w in weights.items() if w >= MAX_SINGLE_WEIGHT}
        for k in capped:
            weights[k] = min(weights[k], MAX_SINGLE_WEIGHT)
        open_names = {k: positives[k] for k in weights if k not in capped and positives[k] > 0}
        open_total = sum(open_names.values())
        if open_total <= 0:
            break
        for k, v in open_names.items():
            weights[k] += excess * v / open_total
    return weights


def _prepare(prices: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    data = prices.copy()
    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True)
    valid = set(SIGNAL_UNIVERSE) | set(TRADE_UNIVERSE)
    data = data[data["symbol"].isin(valid)].sort_values(["timestamp", "symbol"])
    close = data.pivot(index="timestamp", columns="symbol", values="close").sort_index().ffill()
    high = data.pivot(index="timestamp", columns="symbol", values="high").sort_index().ffill()
    low = data.pivot(index="timestamp", columns="symbol", values="low").sort_index().ffill()
    volume = data.pivot(index="timestamp", columns="symbol", values="volume").sort_index().ffill()
    return close, high, low, volume


def _breadth_features(close: pd.DataFrame, high: pd.DataFrame, low: pd.DataFrame, volume: pd.DataFrame) -> dict[str, float]:
    exhaustion = []
    recovery = []
    downside = []
    usable = 0
    for symbol in SIGNAL_UNIVERSE:
        if symbol not in close.columns:
            continue
        c = close[symbol].dropna()
        if len(c) < MIN_HISTORY:
            continue
        idx = c.index
        h = high[symbol].reindex(idx).ffill()
        lo = low[symbol].reindex(idx).ffill()
        v = volume[symbol].reindex(idx).ffill()
        rng = ((h - lo) / c.shift(1)).replace([math.inf, -math.inf], pd.NA).dropna()
        dvol_log = (c * v).apply(lambda x: math.log(max(_safe_float(x), 1.0))).replace([math.inf, -math.inf], pd.NA).dropna()
        ret1 = c.pct_change().replace([math.inf, -math.inf], pd.NA)
        if len(rng) < BASELINE_WINDOW or len(dvol_log) < BASELINE_WINDOW:
            continue
        denom = max(_safe_float(h.iloc[-1] - lo.iloc[-1]), 1e-9)
        clv = _clip(_safe_float((c.iloc[-1] - lo.iloc[-1]) / denom), 0.0, 1.0)
        clv_recent = []
        for j in range(1, RECOVERY_WINDOW + 1):
            den = max(_safe_float(h.iloc[-j] - lo.iloc[-j]), 1e-9)
            clv_recent.append(_clip(_safe_float((c.iloc[-j] - lo.iloc[-j]) / den), 0.0, 1.0))
        range_z = _zscore(_safe_float(rng.iloc[-1]), rng.iloc[-BASELINE_WINDOW - 1 : -1])
        dvol_z = _zscore(_safe_float(dvol_log.iloc[-1]), dvol_log.iloc[-BASELINE_WINDOW - 1 : -1])
        down_move = max(0.0, -_safe_float(ret1.iloc[-1]) / 0.025)
        cap_score = _clip((0.38 * max(0.0, range_z) + 0.34 * max(0.0, dvol_z) + 0.28 * down_move) / 2.6, 0.0, 1.0)
        rec_score = _clip((clv - 0.45) / 0.45 + 0.45 * max(0.0, _mean(clv_recent) - 0.42), 0.0, 1.0)
        exhaustion.append(cap_score)
        recovery.append(rec_score)
        downside.append(1.0 if _safe_float(ret1.iloc[-1]) < -0.0075 else 0.0)
        usable += 1
    return {
        "usable_names": float(usable),
        "exhaustion_breadth": sum(1 for x in exhaustion if x > 0.55) / max(len(exhaustion), 1),
        "mean_exhaustion": _mean(exhaustion),
        "recovery_breadth": sum(1 for x in recovery if x > 0.35) / max(len(recovery), 1),
        "mean_recovery": _mean(recovery),
        "downside_breadth": _mean(downside),
    }


def generate_signals(context) -> dict[str, float]:
    symbols = list(context.symbols)
    if context.prices is None or context.prices.empty:
        return {s: 0.0 for s in symbols}
    close, high, low, volume = _prepare(context.prices)
    if len(close) < MIN_HISTORY:
        return {s: 0.0 for s in symbols}

    available_trades = [s for s in TRADE_UNIVERSE if s in symbols and s in close.columns]
    if len(available_trades) < 8:
        return {s: 0.0 for s in symbols}
    f = _breadth_features(close, high, low, volume)
    if f["usable_names"] < 35:
        return {s: 0.0 for s in symbols}

    recovery_thrust = _clip(
        0.50 * f["exhaustion_breadth"] + 0.25 * f["mean_exhaustion"] + 0.20 * f["recovery_breadth"] + 0.05 * f["downside_breadth"],
        0.0,
        1.0,
    )
    if recovery_thrust < MIN_ACTIVATION:
        return {s: 0.0 for s in symbols}

    gross_budget = _clip(0.25 + 0.85 * recovery_thrust, 0.0, MAX_GROSS)
    recovery_quality = _clip(0.55 * f["recovery_breadth"] + 0.45 * f["mean_recovery"], 0.0, 1.0)
    risk_budget = gross_budget * _clip(0.35 + 0.65 * recovery_quality, 0.25, 0.85)
    defense_budget = gross_budget - risk_budget

    risk_scores: Dict[str, float] = {}
    for etf in RISK_ETFS:
        if etf not in available_trades:
            continue
        trend = _clip(_last_return(close, etf, TREND_WINDOW) / 0.10, -1.0, 1.0)
        vol_penalty = _clip(_realized_vol(close, etf) / 0.35, 0.0, 1.5)
        sector_boost = 0.0
        constituents = SECTOR_MAP.get(etf, ())
        if constituents:
            present = [s for s in constituents if s in close.columns]
            sector_boost = len(present) / max(len(constituents), 1) * recovery_quality
        broad_bonus = 0.25 if etf in {"SPY", "QQQ", "DIA", "USMV", "QUAL"} else 0.0
        risk_scores[etf] = max(0.0, 1.0 + 0.35 * trend + 0.30 * sector_boost + broad_bonus - 0.35 * vol_penalty)

    defense_scores: Dict[str, float] = {}
    for etf in DEFENSIVE_ETFS:
        if etf not in available_trades:
            continue
        trend = _clip(_last_return(close, etf, TREND_WINDOW) / 0.06, -1.0, 1.0)
        vol_penalty = _clip(_realized_vol(close, etf) / 0.25, 0.0, 1.5)
        # Short duration cash-like ETFs are favored when capitulation lacks recovery confirmation.
        cash_bonus = (1.0 - recovery_quality) if etf == "SHY" else 0.0
        defense_scores[etf] = max(0.0, 1.0 + 0.25 * trend + 0.55 * cash_bonus - 0.20 * vol_penalty)

    weights = {s: 0.0 for s in symbols}
    for k, v in _normalize_capped(risk_scores, risk_budget).items():
        weights[k] = weights.get(k, 0.0) + v
    for k, v in _normalize_capped(defense_scores, defense_budget).items():
        weights[k] = weights.get(k, 0.0) + v
    return {s: _safe_float(weights.get(s, 0.0)) for s in symbols}
