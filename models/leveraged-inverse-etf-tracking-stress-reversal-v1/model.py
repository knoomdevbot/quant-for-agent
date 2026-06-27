"""AR-124 leveraged/inverse ETF tracking-stress reversal model.

QFA contract: expose generate_signals(context) -> dict[str, float].

Research-only model.  Leveraged/inverse ETFs are signal inputs only; non-zero
weights are emitted only for unlevered underlying ETFs.  Close-D OHLCV features
are intended to become next-session targets in qfa, and the evaluator shifted
weights by one day to avoid look-ahead.
"""
from __future__ import annotations

import math
from typing import Dict, Iterable

import pandas as pd

# Predeclared broad candidate mappings.  Evaluation filtered these by real
# Alpaca coverage/liquidity before any performance review.
MAPPINGS: tuple[dict, ...] = (
    {"underlying": "SPY", "group": "broad", "pairs": (("SH", -1), ("SDS", -2), ("SSO", 2), ("UPRO", 3), ("SPXU", -3))},
    {"underlying": "QQQ", "group": "broad", "pairs": (("PSQ", -1), ("QID", -2), ("QLD", 2), ("TQQQ", 3), ("SQQQ", -3))},
    {"underlying": "IWM", "group": "broad", "pairs": (("TWM", -2), ("UWM", 2), ("TNA", 3), ("TZA", -3))},
    {"underlying": "XLE", "group": "sector", "pairs": (("ERX", 2), ("ERY", -2))},
    {"underlying": "XLF", "group": "sector", "pairs": (("FAS", 3), ("FAZ", -3))},
    {"underlying": "XLK", "group": "sector", "pairs": (("TECL", 3), ("TECS", -3))},
    {"underlying": "SMH", "group": "sector", "pairs": (("SOXL", 3), ("SOXS", -3))},
    {"underlying": "XBI", "group": "sector", "pairs": (("LABU", 3), ("LABD", -3))},
    {"underlying": "IYR", "group": "sector", "pairs": (("URE", 2), ("SRS", -2))},
    {"underlying": "XRT", "group": "sector", "pairs": (("RETL", 2),)},
    {"underlying": "XHB", "group": "sector", "pairs": (("NAIL", 3),)},
    {"underlying": "TLT", "group": "treasury", "pairs": (("TBT", -2), ("UBT", 2), ("TMF", 3), ("TMV", -3))},
)
UNDERLYINGS = tuple(m["underlying"] for m in MAPPINGS)
SIGNAL_SYMBOLS = tuple({s for m in MAPPINGS for s, _ in m["pairs"]})
LOOKBACK = 60
MIN_LOOKBACK = 40
MIN_HISTORY = 90
EVENT_THRESHOLD = 0.75
MAX_SINGLE_WEIGHT = 0.20


def _finite(value: float, default: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return default
    return out if math.isfinite(out) else default


def _zscore(series: pd.Series, lookback: int = LOOKBACK) -> pd.Series:
    mean = series.rolling(lookback, min_periods=MIN_LOOKBACK).mean()
    std = series.rolling(lookback, min_periods=MIN_LOOKBACK).std()
    return ((series - mean) / std).replace([math.inf, -math.inf], 0.0).fillna(0.0)


def _pivot(prices: pd.DataFrame, field: str) -> pd.DataFrame:
    return prices.pivot(index="timestamp", columns="symbol", values=field).sort_index()


def _normalise(weights: Dict[str, float]) -> Dict[str, float]:
    gross = sum(abs(v) for v in weights.values())
    if gross > 1.0:
        weights = {k: v / gross for k, v in weights.items()}
    return {k: _finite(max(-MAX_SINGLE_WEIGHT, min(MAX_SINGLE_WEIGHT, v))) for k, v in weights.items()}


def _available_pairs(close: pd.DataFrame, underlying: str, pairs: Iterable[tuple[str, int]]) -> list[tuple[str, int]]:
    if underlying not in close.columns:
        return []
    out: list[tuple[str, int]] = []
    for symbol, multiple in pairs:
        if symbol in close.columns and close[[underlying, symbol]].dropna().shape[0] >= MIN_HISTORY:
            out.append((symbol, multiple))
    return out


def generate_signals(context) -> dict[str, float]:
    """Return target weights for unlevered ETFs using pair residual stress.

    The model computes close-to-close residuals r(pair) - multiple*r(underlying),
    z-scores them over 60 sessions, signs them by leverage orientation, scales by
    same-day underlying range/volume stress, and trades a one-day reversal sleeve
    in the unlevered ETF only.  If the qfa run omits the leveraged/inverse signal
    ETFs from context.prices, the model stays in cash.
    """
    symbols = list(context.symbols)
    weights = {symbol: 0.0 for symbol in symbols}
    if getattr(context, "prices", None) is None or context.prices.empty:
        return weights

    prices = context.prices.copy()
    prices["timestamp"] = pd.to_datetime(prices["timestamp"], utc=True)
    close = _pivot(prices, "close").ffill()
    high = _pivot(prices, "high").ffill()
    low = _pivot(prices, "low").ffill()
    volume = _pivot(prices, "volume").ffill()
    if len(close) < MIN_HISTORY:
        return weights

    returns = close.pct_change()
    raw: dict[str, float] = {}
    for mapping in MAPPINGS:
        underlying = mapping["underlying"]
        if underlying not in symbols or underlying not in close.columns:
            continue
        pairs = _available_pairs(close, underlying, mapping["pairs"])
        if not pairs:
            continue

        signed_z: list[pd.Series] = []
        for pair_symbol, multiple in pairs:
            residual = returns[pair_symbol] - float(multiple) * returns[underlying]
            signed_z.append(_zscore(residual) * (1.0 if multiple > 0 else -1.0))
        pressure = pd.concat(signed_z, axis=1).mean(axis=1).clip(-4.0, 4.0)

        day_range = ((high[underlying] - low[underlying]) / close[underlying].shift(1)).replace(
            [math.inf, -math.inf], 0.0
        )
        range_z = _zscore(day_range).clip(lower=0.0)
        log_volume = volume[underlying].replace(0, pd.NA).astype("float64").apply(math.log)
        volume_z = _zscore(log_volume).clip(lower=0.0)
        stress_scale = (0.50 + 0.25 * ((range_z + volume_z) / 2.0).clip(0.0, 3.0)).iloc[-1]
        latest_pressure = _finite(pressure.iloc[-1])
        if abs(latest_pressure) < EVENT_THRESHOLD:
            raw[underlying] = 0.0
        else:
            # Predeclared primary sleeve: reversal of signed residual pressure.
            raw[underlying] = -max(-2.0, min(2.0, latest_pressure)) / 2.0 * _finite(stress_scale, 0.5)

    capped = _normalise({s: raw.get(s, 0.0) for s in UNDERLYINGS if s in symbols})
    for symbol, weight in capped.items():
        weights[symbol] = weight
    # Signal ETFs are deliberately flat if included in the qfa symbol universe.
    return weights
