"""
AR-145 qfa-compatible model wrapper for a CBOE volatility term-structure allocator.

The intended research signal uses externally ingested, point-in-time CBOE volatility
index observations (VIX, VIX3M, VIX9D, VVIX) that have been lagged by at least one
full trading session before being provided to qfa in context.metadata.  The model
contains no embedded CBOE history or market-price data.

Expected context.metadata format for live/evaluation integration:
    {
        "cboe_vol_features": {
            "vix": 18.0,
            "vix3m_vix_ratio": 1.12,
            "vix9d_vix_ratio": 0.92,
            "vvix_percentile_252d": 0.45,
            "vix_percentile_252d": 0.40,
            "post_inversion_normalization": false,
        }
    }

If timestamp-lagged external features are unavailable, generate_signals returns a
cash-like SHY fallback so the qfa contract remains safe and deterministic.
"""

from __future__ import annotations

UNIVERSE = ("SPY", "QQQ", "IWM", "HYG", "LQD", "TLT", "IEF", "GLD", "SHY")

RISK_ON = {"SPY": 0.30, "QQQ": 0.20, "IWM": 0.10, "HYG": 0.15, "LQD": 0.10, "GLD": 0.05, "SHY": 0.10}
DEFENSIVE = {"TLT": 0.25, "IEF": 0.25, "GLD": 0.20, "LQD": 0.10, "SHY": 0.20}
NORMALIZATION = {"SPY": 0.20, "QQQ": 0.15, "HYG": 0.20, "LQD": 0.15, "IEF": 0.10, "GLD": 0.10, "SHY": 0.10}
FALLBACK = {"SHY": 1.0}


def _float(features: dict, key: str, default: float | None = None) -> float | None:
    try:
        value = features.get(key, default)
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return default


def _filter_universe(weights: dict[str, float], symbols: list[str]) -> dict[str, float]:
    allowed = set(symbols or UNIVERSE)
    return {symbol: float(weight) for symbol, weight in weights.items() if symbol in allowed}


def generate_signals(context) -> dict[str, float]:
    """Return target ETF weights from pre-lagged CBOE term-structure features.

    Timestamp discipline is enforced upstream: this function only consumes values
    already present in context.metadata and never downloads or reads external data.
    """

    metadata = getattr(context, "metadata", {}) or {}
    features = metadata.get("cboe_vol_features") or metadata.get("cboe_vol_indices") or {}
    symbols = list(getattr(context, "symbols", []) or UNIVERSE)

    if not isinstance(features, dict) or not features:
        return _filter_universe(FALLBACK, symbols)

    slope = _float(features, "vix3m_vix_ratio")
    short_ratio = _float(features, "vix9d_vix_ratio")
    vvix_pct = _float(features, "vvix_percentile_252d")
    vix_pct = _float(features, "vix_percentile_252d")
    normalizing = bool(features.get("post_inversion_normalization", False))

    if normalizing and (vix_pct is None or vix_pct < 0.85):
        return _filter_universe(NORMALIZATION, symbols)

    stress = False
    if slope is not None and slope < 1.0:
        stress = True
    if short_ratio is not None and short_ratio > 1.02:
        stress = True
    if vvix_pct is not None and vvix_pct >= 0.80:
        stress = True
    if vix_pct is not None and vix_pct >= 0.85:
        stress = True

    if stress:
        return _filter_universe(DEFENSIVE, symbols)

    if slope is not None and slope >= 1.08 and (vvix_pct is None or vvix_pct <= 0.65):
        return _filter_universe(RISK_ON, symbols)

    return _filter_universe(NORMALIZATION, symbols)
