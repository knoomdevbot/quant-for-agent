"""AR-090 Google Trends consumer-attention ETF rotation.

QFA contract: expose generate_signals(context) -> dict[str, float].
The committed model embeds compact, derived monthly Google Trends attention
z-scores only (not raw query series).  The signal applies a one-month
availability lag: a month-start Google Trends feature is first usable on the
next calendar month, avoiding same-month lookahead from normalized/revised data.
"""
from __future__ import annotations

import bisect
import math
from datetime import datetime
from typing import Any

import pandas as pd

UNIVERSE = ["XLY", "XRT", "JETS", "PEJ", "ITB", "IYT", "QQQ", "SPY", "IWM", "XLP", "XLU", "SHY", "GLD", "XLE"]
RISK = ["XLY", "XRT", "JETS", "PEJ", "ITB", "IYT", "QQQ", "SPY", "IWM"]
DEFENSIVE = ["XLP", "XLU", "SHY", "GLD"]
MAX_WEIGHT = 0.30
DERIVED_ATTENTION = [{'month': '2020-07-01', 'travel_attention_z': -0.28299, 'retail_attention_z': 0.260117, 'auto_attention_z': 1.154701, 'consumer_composite_z': 0.288291}, {'month': '2020-08-01', 'travel_attention_z': 0.000171, 'retail_attention_z': 0.360736, 'auto_attention_z': 1.0, 'consumer_composite_z': 0.421053}, {'month': '2020-09-01', 'travel_attention_z': 0.004278, 'retail_attention_z': 0.269175, 'auto_attention_z': 0.447214, 'consumer_composite_z': 0.268857}, {'month': '2020-10-01', 'travel_attention_z': -0.160426, 'retail_attention_z': 0.17997, 'auto_attention_z': -0.136083, 'consumer_composite_z': 0.048686}, {'month': '2020-11-01', 'travel_attention_z': -0.270008, 'retail_attention_z': 0.030677, 'auto_attention_z': -0.755929, 'consumer_composite_z': -0.183462}, {'month': '2020-12-01', 'travel_attention_z': -0.318046, 'retail_attention_z': -0.000321, 'auto_attention_z': -0.707107, 'consumer_composite_z': -0.204389}, {'month': '2021-01-01', 'travel_attention_z': -0.226112, 'retail_attention_z': 0.089979, 'auto_attention_z': -0.707107, 'consumer_composite_z': -0.103713}, {'month': '2021-02-01', 'travel_attention_z': -0.029473, 'retail_attention_z': 0.297394, 'auto_attention_z': -0.169031, 'consumer_composite_z': 0.152756}, {'month': '2021-03-01', 'travel_attention_z': 0.74621, 'retail_attention_z': 0.529729, 'auto_attention_z': 0.333333, 'consumer_composite_z': 0.64074}, {'month': '2021-04-01', 'travel_attention_z': 1.029221, 'retail_attention_z': 0.715576, 'auto_attention_z': 0.845154, 'consumer_composite_z': 0.927978}, {'month': '2021-05-01', 'travel_attention_z': 1.445914, 'retail_attention_z': 0.813674, 'auto_attention_z': 0.845154, 'consumer_composite_z': 1.131669}, {'month': '2021-06-01', 'travel_attention_z': 1.388844, 'retail_attention_z': 0.651848, 'auto_attention_z': 0.845154, 'consumer_composite_z': 0.989197}, {'month': '2021-07-01', 'travel_attention_z': 1.386354, 'retail_attention_z': 0.582512, 'auto_attention_z': 0.845154, 'consumer_composite_z': 0.938351}, {'month': '2021-08-01', 'travel_attention_z': 1.193222, 'retail_attention_z': 0.38773, 'auto_attention_z': 0.845154, 'consumer_composite_z': 0.741344}, {'month': '2021-09-01', 'travel_attention_z': 0.696054, 'retail_attention_z': 0.298768, 'auto_attention_z': 0.169031, 'consumer_composite_z': 0.422936}, {'month': '2021-10-01', 'travel_attention_z': 0.08087, 'retail_attention_z': 0.023273, 'auto_attention_z': 0.0, 'consumer_composite_z': 7e-05}, {'month': '2021-11-01', 'travel_attention_z': -0.350592, 'retail_attention_z': -0.09287, 'auto_attention_z': -0.19245, 'consumer_composite_z': -0.247092}, {'month': '2021-12-01', 'travel_attention_z': -0.379118, 'retail_attention_z': -0.190926, 'auto_attention_z': -0.19245, 'consumer_composite_z': -0.334449}, {'month': '2022-01-01', 'travel_attention_z': 0.072406, 'retail_attention_z': -0.259548, 'auto_attention_z': -0.447214, 'consumer_composite_z': -0.238648}, {'month': '2022-02-01', 'travel_attention_z': 0.560815, 'retail_attention_z': -0.045886, 'auto_attention_z': -0.447214, 'consumer_composite_z': 0.087788}, {'month': '2022-03-01', 'travel_attention_z': 0.848919, 'retail_attention_z': 0.116305, 'auto_attention_z': 0.447214, 'consumer_composite_z': 0.480974}, {'month': '2022-04-01', 'travel_attention_z': 0.882072, 'retail_attention_z': 0.275999, 'auto_attention_z': 0.447214, 'consumer_composite_z': 0.578473}, {'month': '2022-05-01', 'travel_attention_z': 0.628297, 'retail_attention_z': 0.09587, 'auto_attention_z': 0.447214, 'consumer_composite_z': 0.349408}, {'month': '2022-06-01', 'travel_attention_z': 0.586167, 'retail_attention_z': -0.065221, 'auto_attention_z': 0.447214, 'consumer_composite_z': 0.162811}, {'month': '2022-07-01', 'travel_attention_z': 0.670762, 'retail_attention_z': 0.108382, 'auto_attention_z': 0.447214, 'consumer_composite_z': 0.2727}, {'month': '2022-08-01', 'travel_attention_z': 0.406324, 'retail_attention_z': 0.095057, 'auto_attention_z': 0.447214, 'consumer_composite_z': 0.175483}, {'month': '2022-09-01', 'travel_attention_z': -0.3888, 'retail_attention_z': -0.210878, 'auto_attention_z': 0.301511, 'consumer_composite_z': -0.291434}, {'month': '2022-10-01', 'travel_attention_z': -1.12305, 'retail_attention_z': -0.51171, 'auto_attention_z': -0.447214, 'consumer_composite_z': -0.812453}, {'month': '2022-11-01', 'travel_attention_z': -1.424457, 'retail_attention_z': -0.736417, 'auto_attention_z': -0.96225, 'consumer_composite_z': -1.115455}, {'month': '2022-12-01', 'travel_attention_z': -1.277331, 'retail_attention_z': -0.520154, 'auto_attention_z': -1.732051, 'consumer_composite_z': -1.025626}, {'month': '2023-01-01', 'travel_attention_z': -0.931308, 'retail_attention_z': -0.332064, 'auto_attention_z': -0.96225, 'consumer_composite_z': -0.645103}, {'month': '2023-02-01', 'travel_attention_z': -0.360115, 'retail_attention_z': 0.049584, 'auto_attention_z': -0.19245, 'consumer_composite_z': -0.092327}, {'month': '2023-03-01', 'travel_attention_z': 0.11681, 'retail_attention_z': -0.035771, 'auto_attention_z': 0.57735, 'consumer_composite_z': 0.114966}, {'month': '2023-04-01', 'travel_attention_z': 0.060585, 'retail_attention_z': -0.049154, 'auto_attention_z': 0.57735, 'consumer_composite_z': 0.090603}, {'month': '2023-05-01', 'travel_attention_z': 0.075734, 'retail_attention_z': -0.058818, 'auto_attention_z': 0.57735, 'consumer_composite_z': 0.092523}, {'month': '2023-06-01', 'travel_attention_z': 0.284832, 'retail_attention_z': 0.271543, 'auto_attention_z': 0.57735, 'consumer_composite_z': 0.3874}, {'month': '2023-07-01', 'travel_attention_z': 0.700689, 'retail_attention_z': 0.540754, 'auto_attention_z': 0.57735, 'consumer_composite_z': 0.668137}, {'month': '2023-08-01', 'travel_attention_z': 0.652425, 'retail_attention_z': 0.537675, 'auto_attention_z': 0.57735, 'consumer_composite_z': 0.650167}, {'month': '2023-09-01', 'travel_attention_z': -0.09425, 'retail_attention_z': 0.352604, 'auto_attention_z': 0.57735, 'consumer_composite_z': 0.312707}, {'month': '2023-10-01', 'travel_attention_z': -0.802854, 'retail_attention_z': -0.265004, 'auto_attention_z': -0.19245, 'consumer_composite_z': -0.447845}, {'month': '2023-11-01', 'travel_attention_z': -1.165504, 'retail_attention_z': -0.418018, 'auto_attention_z': -0.447214, 'consumer_composite_z': -0.697378}, {'month': '2023-12-01', 'travel_attention_z': -1.096082, 'retail_attention_z': -0.342217, 'auto_attention_z': -0.904534, 'consumer_composite_z': -0.715149}, {'month': '2024-01-01', 'travel_attention_z': -0.699337, 'retail_attention_z': -0.119423, 'auto_attention_z': 0.301511, 'consumer_composite_z': -0.215985}, {'month': '2024-02-01', 'travel_attention_z': -0.245002, 'retail_attention_z': -0.075138, 'auto_attention_z': 0.301511, 'consumer_composite_z': -0.041468}, {'month': '2024-03-01', 'travel_attention_z': 0.382255, 'retail_attention_z': 0.017758, 'auto_attention_z': 0.301511, 'consumer_composite_z': 0.261295}, {'month': '2024-04-01', 'travel_attention_z': 0.447398, 'retail_attention_z': 0.208977, 'auto_attention_z': 0.301511, 'consumer_composite_z': 0.410638}, {'month': '2024-05-01', 'travel_attention_z': 0.265256, 'retail_attention_z': 0.232547, 'auto_attention_z': 0.301511, 'consumer_composite_z': 0.355138}, {'month': '2024-06-01', 'travel_attention_z': 0.354282, 'retail_attention_z': 0.061411, 'auto_attention_z': 0.301511, 'consumer_composite_z': 0.235946}, {'month': '2024-07-01', 'travel_attention_z': 0.587921, 'retail_attention_z': 0.275643, 'auto_attention_z': 0.301511, 'consumer_composite_z': 0.392701}, {'month': '2024-08-01', 'travel_attention_z': 0.364173, 'retail_attention_z': 0.469812, 'auto_attention_z': 0.301511, 'consumer_composite_z': 0.442142}, {'month': '2024-09-01', 'travel_attention_z': -0.233129, 'retail_attention_z': 0.451241, 'auto_attention_z': 0.301511, 'consumer_composite_z': 0.281923}, {'month': '2024-10-01', 'travel_attention_z': -0.894601, 'retail_attention_z': 0.054824, 'auto_attention_z': -0.904534, 'consumer_composite_z': -0.353538}, {'month': '2024-11-01', 'travel_attention_z': -0.964216, 'retail_attention_z': -0.152917, 'auto_attention_z': -0.904534, 'consumer_composite_z': -0.476677}, {'month': '2024-12-01', 'travel_attention_z': -0.989789, 'retail_attention_z': -0.205141, 'auto_attention_z': -0.904534, 'consumer_composite_z': -0.528551}, {'month': '2025-01-01', 'travel_attention_z': -0.159689, 'retail_attention_z': 0.01367, 'auto_attention_z': 0.301511, 'consumer_composite_z': 0.100186}, {'month': '2025-02-01', 'travel_attention_z': 0.385179, 'retail_attention_z': 0.038216, 'auto_attention_z': 0.301511, 'consumer_composite_z': 0.280017}, {'month': '2025-03-01', 'travel_attention_z': 0.727147, 'retail_attention_z': 0.087349, 'auto_attention_z': 0.301511, 'consumer_composite_z': 0.416903}, {'month': '2025-04-01', 'travel_attention_z': 0.760762, 'retail_attention_z': 0.156288, 'auto_attention_z': 0.301511, 'consumer_composite_z': 0.452797}, {'month': '2025-05-01', 'travel_attention_z': 0.86731, 'retail_attention_z': 0.312729, 'auto_attention_z': 0.301511, 'consumer_composite_z': 0.585014}, {'month': '2025-06-01', 'travel_attention_z': 0.926118, 'retail_attention_z': 0.522602, 'auto_attention_z': 0.301511, 'consumer_composite_z': 0.73418}, {'month': '2025-07-01', 'travel_attention_z': 1.266, 'retail_attention_z': 0.763275, 'auto_attention_z': 0.816497, 'consumer_composite_z': 1.061638}, {'month': '2025-08-01', 'travel_attention_z': 1.423211, 'retail_attention_z': 0.867816, 'auto_attention_z': 0.816497, 'consumer_composite_z': 1.164869}, {'month': '2025-09-01', 'travel_attention_z': 0.792252, 'retail_attention_z': 0.725594, 'auto_attention_z': 0.816497, 'consumer_composite_z': 0.879854}, {'month': '2025-10-01', 'travel_attention_z': -0.119154, 'retail_attention_z': 0.437658, 'auto_attention_z': -0.301511, 'consumer_composite_z': 0.242004}, {'month': '2025-11-01', 'travel_attention_z': -0.110575, 'retail_attention_z': 0.642565, 'auto_attention_z': 0.447214, 'consumer_composite_z': 0.409163}, {'month': '2025-12-01', 'travel_attention_z': 0.443245, 'retail_attention_z': 0.953064, 'auto_attention_z': 0.96225, 'consumer_composite_z': 0.791539}]
_MONTHS = [r["month"] for r in DERIVED_ATTENTION]


def _pivot(prices: pd.DataFrame, field: str) -> pd.DataFrame:
    px = prices.copy()
    px["timestamp"] = pd.to_datetime(px["timestamp"], utc=True)
    return px.pivot(index="timestamp", columns="symbol", values=field).sort_index().ffill()


def _safe(v: Any, default: float = 0.0) -> float:
    try:
        f = float(v)
    except Exception:
        return default
    return f if math.isfinite(f) else default


def _ret(close: pd.DataFrame, sym: str, n: int) -> float:
    if sym not in close:
        return 0.0
    s = close[sym].dropna()
    if len(s) <= n:
        return 0.0
    return _safe(s.iloc[-1] / s.iloc[-1 - n] - 1.0)


def _current_date_from_context(context: Any, prices: pd.DataFrame) -> datetime | None:
    for name in ("timestamp", "current_time", "now", "date"):
        v = getattr(context, name, None)
        if v is not None:
            try:
                return pd.Timestamp(v).to_pydatetime()
            except Exception:
                pass
    if prices is not None and len(prices):
        return pd.to_datetime(prices["timestamp"]).max().to_pydatetime()
    return None


def _lagged_attention(asof: datetime) -> dict[str, float]:
    # Feature for month M is only available from month M+1 onward.  Therefore
    # use strictly prior month_start relative to asof's current month_start.
    month_start = f"{asof.year:04d}-{asof.month:02d}-01"
    idx = bisect.bisect_left(_MONTHS, month_start) - 1
    if idx < 0:
        return {}
    return DERIVED_ATTENTION[idx]


def _cap_normalize(raw: dict[str, float], symbols: list[str]) -> dict[str, float]:
    vals = {s: max(0.0, _safe(raw.get(s, 0.0))) for s in symbols}
    gross = sum(vals.values())
    if gross <= 0:
        return {s: (1.0 if s == "SHY" else 0.0) for s in symbols}
    w = {s: vals[s] / gross for s in symbols}
    for _ in range(8):
        excess = sum(max(0.0, v - MAX_WEIGHT) for v in w.values())
        w = {s: min(v, MAX_WEIGHT) for s, v in w.items()}
        room = {s: MAX_WEIGHT - v for s, v in w.items() if v < MAX_WEIGHT - 1e-12}
        if excess <= 1e-12 or not room:
            break
        rt = sum(room.values())
        for s, r in room.items():
            w[s] += excess * r / rt
    g = sum(w.values())
    return {s: (v / g if g > 0 else 0.0) for s, v in w.items()}


def generate_signals(context: Any) -> dict[str, float]:
    """Return long-only ETF target weights from lagged Trends attention.

    Positive consumer attention tilts to discretionary/retail/travel/risk ETFs
    if price confirmation is positive. Negative attention or missing history
    falls back to defensive/cash-like ETFs. Uses only qfa-provided daily OHLCV
    for market confirmation; no orders are placed by this model.
    """
    symbols = list(getattr(context, "symbols", UNIVERSE) or UNIVERSE)
    prices = getattr(context, "prices", None)
    out = {s: 0.0 for s in symbols}
    if prices is None or len(prices) < 80:
        return out
    asof = _current_date_from_context(context, prices)
    if asof is None:
        return out
    att = _lagged_attention(asof)
    close = _pivot(prices, "close").reindex(columns=[s for s in symbols if s in UNIVERSE]).ffill()
    if close.empty:
        return out
    raw: dict[str, float] = {}
    comp = _safe(att.get("consumer_composite_z"), 0.0)
    travel = _safe(att.get("travel_attention_z"), 0.0)
    retail = _safe(att.get("retail_attention_z"), 0.0)
    auto = _safe(att.get("auto_attention_z"), 0.0)
    risk_gate = 0.55 * _ret(close, "SPY", 60) + 0.45 * _ret(close, "QQQ", 60)
    if comp > 0.15 and risk_gate > -0.03:
        theme = {
            "XLY": 0.55 * comp + 0.30 * retail + 0.15 * auto,
            "XRT": 0.45 * comp + 0.45 * retail,
            "JETS": 0.35 * comp + 0.65 * travel,
            "PEJ": 0.40 * comp + 0.45 * travel + 0.15 * retail,
            "ITB": 0.30 * comp + 0.55 * auto,
            "IYT": 0.30 * comp + 0.50 * travel,
            "QQQ": 0.45 * comp,
            "SPY": 0.35 * comp,
            "IWM": 0.30 * comp + 0.20 * retail,
        }
        for s, score in theme.items():
            if s in close and s in symbols:
                mom = 0.60 * _ret(close, s, 20) + 0.40 * _ret(close, s, 60)
                if mom > -0.04:
                    raw[s] = max(0.0, score) * (1.0 + max(mom, 0.0) * 3.0)
    if not raw:
        for s in DEFENSIVE:
            if s in close and s in symbols:
                mom = 0.5 * _ret(close, s, 20) + 0.5 * _ret(close, s, 60)
                raw[s] = 0.25 + max(mom, 0.0) * 2.0
    return {s: float(_cap_normalize(raw, symbols).get(s, 0.0)) for s in symbols}
