"""Adaptive residual pair mean-reversion alpha for mega-cap tech equities.

QFA contract: expose generate_signals(context) -> dict[symbol, weight].
Research-only model; it does not place orders or call any broker/trading API.
"""
from __future__ import annotations

import itertools
import math

import pandas as pd

UNIVERSE = ("AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL")
ALL_PAIRS = tuple(itertools.combinations(UNIVERSE, 2))


class ModelParams:
    formation_window = 180
    z_window = 45
    corr_window = 90
    min_pair_observations = 150
    min_symbols = 4
    min_corr = 0.55
    max_adf_ar1_phi = 0.985
    max_half_life_days = 45.0
    min_zero_crossings = 3
    entry_z = 1.75
    max_z = 3.0
    max_pairs = 3
    max_abs_weight = 0.30


PARAMS = ModelParams()


def _zero_weights(symbols):
    return {symbol: 0.0 for symbol in symbols}


def _log_or_nan(value: float) -> float:
    value = float(value)
    return math.log(value) if math.isfinite(value) and value > 0 else float("nan")


def _cap_and_normalize(weights: dict[str, float], max_abs_weight: float) -> dict[str, float]:
    clean = {s: float(w) for s, w in weights.items() if math.isfinite(float(w))}
    gross = sum(abs(w) for w in clean.values())
    if not clean or gross <= 0:
        return {s: 0.0 for s in weights}
    normalized = {s: w / gross for s, w in clean.items()}
    capped = {s: max(-max_abs_weight, min(max_abs_weight, w)) for s, w in normalized.items()}
    capped_gross = sum(abs(w) for w in capped.values())
    if capped_gross <= 0:
        return {s: 0.0 for s in weights}
    return {s: float(capped.get(s, 0.0) / capped_gross) for s in weights}


def _ols_residual(log_close: pd.DataFrame, y: str, x: str) -> tuple[pd.Series | None, float]:
    pair = log_close[[y, x]].dropna()
    if len(pair) < PARAMS.min_pair_observations:
        return None, 0.0
    formation = pair.iloc[-PARAMS.formation_window :]
    y_series = formation[y]
    x_series = formation[x]
    x_var = float(x_series.var(ddof=0))
    if not math.isfinite(x_var) or x_var <= 0:
        return None, 0.0
    beta = float(x_series.cov(y_series) / x_var)
    alpha = float(y_series.mean() - beta * x_series.mean())
    residual = pair[y] - (alpha + beta * pair[x])
    return residual.dropna(), beta


def _ar1_phi(residual: pd.Series) -> float:
    values = residual.dropna()
    if len(values) < 40:
        return float("nan")
    y = values.diff().dropna()
    lagged = values.shift(1).dropna().loc[y.index]
    denom = float((lagged * lagged).sum())
    if denom <= 0:
        return float("nan")
    gamma = float((lagged * y).sum() / denom)
    return 1.0 + gamma


def _half_life(phi: float) -> float:
    if not math.isfinite(phi) or phi <= 0 or phi >= 1:
        return float("inf")
    return float(-math.log(2.0) / math.log(phi))


def _zero_crossings(residual: pd.Series) -> int:
    centered = residual - residual.mean()
    signs = centered.apply(lambda v: 1 if v > 0 else (-1 if v < 0 else 0))
    signs = signs[signs != 0]
    if len(signs) < 2:
        return 0
    return int((signs * signs.shift(1) < 0).sum())


def _pair_candidate(log_close: pd.DataFrame, returns: pd.DataFrame, y: str, x: str) -> dict | None:
    if y not in log_close.columns or x not in log_close.columns:
        return None
    pair_returns = returns[[y, x]].dropna().iloc[-PARAMS.corr_window :]
    if len(pair_returns) < 40:
        return None
    corr = float(pair_returns[y].corr(pair_returns[x]))
    if not math.isfinite(corr) or corr < PARAMS.min_corr:
        return None

    residual, beta = _ols_residual(log_close, y, x)
    if residual is None or len(residual) < max(PARAMS.z_window, 40):
        return None
    recent = residual.iloc[-PARAMS.z_window :]
    resid_std = float(recent.std(ddof=0))
    if not math.isfinite(resid_std) or resid_std <= 0:
        return None
    z_score = float((recent.iloc[-1] - recent.mean()) / resid_std)
    if not math.isfinite(z_score) or abs(z_score) < PARAMS.entry_z:
        return None

    phi = _ar1_phi(residual.iloc[-PARAMS.formation_window :])
    hl = _half_life(phi)
    crossings = _zero_crossings(residual.iloc[-PARAMS.formation_window :])
    if not (math.isfinite(phi) and phi < PARAMS.max_adf_ar1_phi and hl <= PARAMS.max_half_life_days and crossings >= PARAMS.min_zero_crossings):
        return None

    # Higher score favors correlated pairs with faster residual reversion and larger but clipped dislocation.
    score = abs(z_score) * max(corr, 0.0) * min(2.0, max(0.25, PARAMS.max_half_life_days / max(hl, 1.0)))
    return {"pair": (y, x), "z": z_score, "beta": beta, "corr": corr, "phi": phi, "half_life": hl, "crossings": crossings, "score": score}


def generate_signals(context):
    """Return target weights from adaptively selected cointegration-like pair residuals.

    Pair eligibility requires high rolling return correlation plus residual-stability gates:
    AR(1) residual persistence below 0.985, half-life <= 45 sessions, and at least
    three residual zero-crossings in the 180-session formation window. The model
    trades only the strongest three eligible dislocations and gross-normalizes.
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
        .dropna(axis=1, how="any")
    )
    tradable = [s for s in symbols if s in close.columns]
    if len(tradable) < PARAMS.min_symbols or len(close) < PARAMS.min_pair_observations:
        return _zero_weights(output_symbols)

    log_close = close[tradable].map(_log_or_nan).dropna(axis=1, how="any")
    tradable = [s for s in tradable if s in log_close.columns]
    if len(tradable) < PARAMS.min_symbols:
        return _zero_weights(output_symbols)
    returns = close[tradable].pct_change()

    candidates = []
    for y, x in ALL_PAIRS:
        if y not in tradable or x not in tradable:
            continue
        candidate = _pair_candidate(log_close, returns, y, x)
        if candidate:
            candidates.append(candidate)
    if not candidates:
        return _zero_weights(output_symbols)

    selected = sorted(candidates, key=lambda c: c["score"], reverse=True)[: PARAMS.max_pairs]
    scores = {s: 0.0 for s in output_symbols}
    for candidate in selected:
        y, x = candidate["pair"]
        strength = max(-PARAMS.max_z, min(PARAMS.max_z, candidate["z"]))
        # High residual: y rich vs x -> short y, long x; low residual reverses signs.
        scores[y] += -strength * candidate["score"]
        scores[x] += strength * candidate["score"]

    tradable_scores = pd.Series({s: scores.get(s, 0.0) for s in tradable}, dtype=float)
    tradable_scores = tradable_scores - tradable_scores.mean()
    raw = {s: float(tradable_scores.get(s, 0.0)) for s in output_symbols}
    return _cap_and_normalize(raw, PARAMS.max_abs_weight)
