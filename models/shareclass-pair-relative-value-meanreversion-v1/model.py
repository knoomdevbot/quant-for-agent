"""AR-132 share-class pair relative-value mean reversion model.

QFA contract: expose generate_signals(context) -> dict[str, float].
Research-only model; it never places orders.

Economics: listed same-issuer share classes with similar cash-flow exposure may
exhibit temporary relative-price dislocations from liquidity, voting/index demand,
and microstructure. The model computes a prior-only log-price-ratio z-score for
fixed ex-ante pairs, goes long the cheap class and short the rich class, and
gross-normalizes across active pairs.
"""

from __future__ import annotations

import math

import pandas as pd


class Params:
    zscore_window: int = 120
    entry_z: float = 1.0
    decay_days: int = 3
    max_symbol_abs_weight: float = 0.25
    min_active_pairs: int = 1


PARAMS = Params()

# Fixed before performance review from known U.S.-listed same-issuer share classes.
# The evaluation artifact documents data/liquidity exclusions; generate_signals can
# accept any subset provided by qfa and will ignore unavailable legs.
PAIRS: tuple[tuple[str, str], ...] = (
    ("GOOGL", "GOOG"),
    ("FOXA", "FOX"),
    ("NWSA", "NWS"),
    ("BATRA", "BATRK"),
    ("LBRDA", "LBRDK"),
    ("FWONA", "FWONK"),
    ("LILA", "LILAK"),
    ("LEN", "LEN.B"),
    ("HEI", "HEI.A"),
    ("UHAL", "UHAL.B"),
    ("BF.A", "BF.B"),
)


def _zero(symbols: list[str]) -> dict[str, float]:
    return {s: 0.0 for s in symbols}


def _wide_close(prices: pd.DataFrame, symbols: list[str]) -> pd.DataFrame:
    px = prices[prices["symbol"].isin(symbols)].copy()
    if px.empty:
        return pd.DataFrame()
    px["timestamp"] = pd.to_datetime(px["timestamp"], utc=True)
    return px.pivot_table(index="timestamp", columns="symbol", values="close", aggfunc="last").sort_index().ffill()


def _cap_and_normalize(weights: dict[str, float], max_abs_weight: float) -> dict[str, float]:
    clean = {s: float(w) for s, w in weights.items() if math.isfinite(float(w))}
    gross = sum(abs(w) for w in clean.values())
    if gross <= 0.0:
        return {s: 0.0 for s in weights}
    scaled = {s: w / gross for s, w in clean.items()}
    capped = {s: max(-max_abs_weight, min(max_abs_weight, w)) for s, w in scaled.items()}
    capped_gross = sum(abs(w) for w in capped.values())
    if capped_gross <= 0.0:
        return {s: 0.0 for s in weights}
    return {s: float(capped.get(s, 0.0) / capped_gross) for s in weights}


def generate_signals(context) -> dict[str, float]:
    """Return share-class pair mean-reversion target weights.

    Uses only completed bars in ``context.prices``. For each available pair:
    spread = log(price_a) - log(price_b). If the latest prior-only z-score is
    positive, class A is rich vs class B, so the model shorts A/longs B; if
    negative it does the reverse. A 3-day rolling average of thresholded scores
    provides the decay/holding proxy used in evaluation.
    """
    output_symbols = list(context.symbols)
    if getattr(context, "prices", pd.DataFrame()).empty:
        return _zero(output_symbols)

    required = sorted({s for pair in PAIRS for s in pair if s in set(output_symbols)})
    if not required:
        return _zero(output_symbols)

    close = _wide_close(context.prices, required)
    if close.empty or len(close) < PARAMS.zscore_window + PARAMS.decay_days + 2:
        return _zero(output_symbols)

    raw = {s: 0.0 for s in output_symbols}
    active_pairs = 0
    for a, b in PAIRS:
        if a not in close.columns or b not in close.columns:
            continue
        pair_close = close[[a, b]].dropna()
        if len(pair_close) < PARAMS.zscore_window + PARAMS.decay_days + 2:
            continue
        spread = (pd.Series(pair_close[a], index=pair_close.index).map(math.log) - pd.Series(pair_close[b], index=pair_close.index).map(math.log)).replace([float("inf"), float("-inf")], pd.NA)
        mu = spread.shift(1).rolling(PARAMS.zscore_window, min_periods=PARAMS.zscore_window).mean()
        sd = spread.shift(1).rolling(PARAMS.zscore_window, min_periods=PARAMS.zscore_window).std(ddof=0)
        z = ((spread.shift(1) - mu) / sd.replace(0.0, pd.NA)).dropna()
        if z.empty:
            continue
        signal = (-z / PARAMS.entry_z).clip(-1.0, 1.0).where(z.abs() >= PARAMS.entry_z, 0.0)
        if PARAMS.decay_days > 1:
            signal = signal.rolling(PARAMS.decay_days, min_periods=1).mean()
        latest_score = float(signal.iloc[-1]) if len(signal) else 0.0
        if not math.isfinite(latest_score) or abs(latest_score) <= 1e-12:
            continue
        raw[a] = raw.get(a, 0.0) + 0.5 * latest_score
        raw[b] = raw.get(b, 0.0) - 0.5 * latest_score
        active_pairs += 1

    if active_pairs < PARAMS.min_active_pairs:
        return _zero(output_symbols)
    return _cap_and_normalize(raw, PARAMS.max_symbol_abs_weight)
