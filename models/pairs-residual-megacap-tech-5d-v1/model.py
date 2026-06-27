"""Residual mean-reversion alpha for mega-cap tech equity pairs.

QFA contract: expose generate_signals(context) -> dict[symbol, weight].
Research-only model; it does not place orders or call any broker/trading API.
"""

from __future__ import annotations

import itertools
import math

import pandas as pd


UNIVERSE = ("AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL")


class ModelParams:
    formation_window = 126
    z_window = 60
    entry_z = 1.5
    exit_z = 0.5
    max_abs_weight = 0.25
    min_symbols = 4
    min_pair_observations = 100


PARAMS = ModelParams()

# Broad liquid growth/mega-cap tech pair basket.  Signals are symmetric: if the
# residual y - beta*x is high, short y and long x; if low, long y and short x.
PAIRS = tuple(itertools.combinations(UNIVERSE, 2))


def _zero_weights(symbols):
    return {symbol: 0.0 for symbol in symbols}


def _cap_and_normalize(weights: dict[str, float], max_abs_weight: float) -> dict[str, float]:
    clean = {s: float(w) for s, w in weights.items() if math.isfinite(float(w))}
    gross = sum(abs(w) for w in clean.values())
    if not clean or gross <= 0:
        return {s: 0.0 for s in weights}

    # First normalize to unit gross, cap, then renormalize uncapped residual when feasible.
    normalized = {s: w / gross for s, w in clean.items()}
    capped = {s: max(-max_abs_weight, min(max_abs_weight, w)) for s, w in normalized.items()}
    capped_gross = sum(abs(w) for w in capped.values())
    if capped_gross <= 0:
        return {s: 0.0 for s in weights}
    if capped_gross < 0.999:
        uncapped = {s: normalized[s] for s in normalized if abs(capped[s]) < max_abs_weight - 1e-12}
        fixed_gross = sum(abs(w) for s, w in capped.items() if s not in uncapped)
        target = max(0.0, 1.0 - fixed_gross)
        uncapped_gross = sum(abs(w) for w in uncapped.values())
        if uncapped and uncapped_gross > 0 and target > 0:
            for s in uncapped:
                capped[s] = uncapped[s] / uncapped_gross * target
    return {s: float(capped.get(s, 0.0)) for s in weights}


def _pair_signal(log_close: pd.DataFrame, y: str, x: str) -> tuple[float, float]:
    pair = log_close[[y, x]].dropna()
    required = max(PARAMS.formation_window, PARAMS.z_window) + 1
    if len(pair) < max(required, PARAMS.min_pair_observations):
        return 0.0, 0.0

    formation = pair.iloc[-PARAMS.formation_window :]
    y_series = formation[y]
    x_series = formation[x]
    x_var = float(x_series.var(ddof=0))
    if not math.isfinite(x_var) or x_var <= 0:
        return 0.0, 0.0

    beta = float(x_series.cov(y_series) / x_var)
    alpha = float(y_series.mean() - beta * x_series.mean())
    residual = pair[y] - (alpha + beta * pair[x])
    recent = residual.iloc[-PARAMS.z_window :]
    resid_std = float(recent.std(ddof=0))
    if not math.isfinite(resid_std) or resid_std <= 0:
        return 0.0, 0.0

    z_score = float((recent.iloc[-1] - recent.mean()) / resid_std)
    if not math.isfinite(z_score) or abs(z_score) < PARAMS.entry_z or abs(z_score) <= PARAMS.exit_z:
        return 0.0, 0.0

    # Signal strength grows with residual stretch but is clipped to reduce crowding/tail exposure.
    strength = max(-3.0, min(3.0, z_score))
    # High residual: y rich vs x -> short y, long x. Low residual: long y, short x.
    return -strength, strength


def generate_signals(context):
    """Return target long/short weights from residual pair mean reversion.

    The model estimates rolling log-price hedge ratios over a 126-session formation
    window, scores the latest pair residual against its 60-session residual history,
    enters when |z| >= 1.5, aggregates pair legs, then gross-normalizes to 1.0 with
    a 25% single-name cap.
    """
    output_symbols = list(context.symbols)
    symbols = [s for s in output_symbols if s in UNIVERSE]
    if len(symbols) < PARAMS.min_symbols:
        return _zero_weights(output_symbols)

    prices = context.prices.copy()
    if prices.empty:
        return _zero_weights(output_symbols)
    prices["timestamp"] = pd.to_datetime(prices["timestamp"], utc=True)
    close = (
        prices[prices["symbol"].isin(symbols)]
        .pivot(index="timestamp", columns="symbol", values="close")
        .sort_index()
        .ffill()
    )
    close = close.dropna(axis=1, how="any")
    tradable = [s for s in symbols if s in close.columns]
    if len(tradable) < PARAMS.min_symbols or len(close) < PARAMS.formation_window + 1:
        return _zero_weights(output_symbols)

    log_close = close[tradable].map(lambda v: math.log(float(v)) if float(v) > 0 else float("nan"))
    scores = {s: 0.0 for s in output_symbols}
    active_pairs = 0
    for y, x in PAIRS:
        if y not in tradable or x not in tradable:
            continue
        y_sig, x_sig = _pair_signal(log_close, y, x)
        if y_sig == 0.0 and x_sig == 0.0:
            continue
        scores[y] += y_sig
        scores[x] += x_sig
        active_pairs += 1

    if active_pairs == 0:
        return _zero_weights(output_symbols)

    # Remove residual net market bias from aggregated pair signals.
    tradable_scores = pd.Series({s: scores.get(s, 0.0) for s in tradable}, dtype=float)
    tradable_scores = tradable_scores - tradable_scores.mean()
    raw = {s: float(tradable_scores.get(s, 0.0)) for s in output_symbols}
    return _cap_and_normalize(raw, PARAMS.max_abs_weight)
