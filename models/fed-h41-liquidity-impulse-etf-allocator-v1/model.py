from __future__ import annotations

RISK_ON = {"SPY": 0.25, "QQQ": 0.20, "IWM": 0.15, "HYG": 0.20, "LQD": 0.10, "GLD": 0.10}
DEFENSIVE = {"TLT": 0.25, "IEF": 0.25, "SHY": 0.25, "GLD": 0.15, "UUP": 0.10}
NEUTRAL = {"SPY": 0.15, "QQQ": 0.10, "HYG": 0.10, "LQD": 0.15, "IEF": 0.20, "SHY": 0.20, "GLD": 0.10}

def _get_impulse(context):
    if isinstance(context, dict):
        for key in ("h41_liquidity_impulse_z", "liquidity_impulse_z", "impulse_z"):
            if key in context and context[key] is not None:
                return float(context[key])
        features = context.get("features") or {}
        if isinstance(features, dict):
            for key in ("h41_liquidity_impulse_z", "liquidity_impulse_z", "impulse_z"):
                if key in features and features[key] is not None:
                    return float(features[key])
    return None

def generate_signals(context):
    """Return ETF target weights for a precomputed, timestamp-safe H.4.1 impulse.

    Callers must supply a release-lagged impulse z-score computed only after the
    public Thursday 16:30 ET H.4.1 release. Without it, stay in SHY.
    """
    z = _get_impulse(context)
    if z is None:
        return {"SHY": 1.0}
    if z >= 0.75:
        return dict(RISK_ON)
    if z <= -0.75:
        return dict(DEFENSIVE)
    return dict(NEUTRAL)
