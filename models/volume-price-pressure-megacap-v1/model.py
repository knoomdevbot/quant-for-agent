"""Volume-confirmed price pressure continuation alpha for mega-cap equities.

QFA contract: expose generate_signals(context) -> dict[symbol, weight].
Research-only model; it never places orders.
"""

from __future__ import annotations

import math

import pandas as pd

UNIVERSE = ("AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA")


class ModelParams:
    # AR-009 seed parameter choice from issue search space.
    return_window = 3
    volume_z_window = 60
    volume_z_min = 1.0
    dollar_volume_z_min = 1.0
    max_abs_weight = 0.25
    min_symbols = 3


PARAMS = ModelParams()


def _zero_weights(symbols):
    return {symbol: 0.0 for symbol in symbols}


def _cap_and_normalize(weights: dict[str, float], max_abs_weight: float) -> dict[str, float]:
    """Gross-normalize weights to 1.0 and cap per-name absolute weights where feasible."""
    clean = {s: float(w) for s, w in weights.items() if math.isfinite(float(w))}
    if not clean or sum(abs(w) for w in clean.values()) <= 0.0:
        return {s: 0.0 for s in weights}

    signs = {s: 1.0 if w >= 0 else -1.0 for s, w in clean.items()}
    magnitudes = {s: abs(w) for s, w in clean.items()}
    capped: dict[str, float] = {}
    remaining = set(magnitudes)
    remaining_gross = 1.0

    while remaining:
        total_mag = sum(magnitudes[s] for s in remaining)
        if total_mag <= 0.0 or remaining_gross <= 0.0:
            break
        tentative = {s: remaining_gross * magnitudes[s] / total_mag for s in remaining}
        violators = {s for s, mag in tentative.items() if mag > max_abs_weight}
        if not violators:
            capped.update(tentative)
            break
        for symbol in violators:
            capped[symbol] = max_abs_weight
            remaining.remove(symbol)
            remaining_gross -= max_abs_weight

    return {s: float(signs.get(s, 1.0) * capped.get(s, 0.0)) for s in weights}


def _wide(prices: pd.DataFrame, symbols: list[str]):
    px = prices[prices["symbol"].isin(symbols)].copy()
    if px.empty:
        return None
    px["timestamp"] = pd.to_datetime(px["timestamp"], utc=True)
    px = px.sort_values(["timestamp", "symbol"])
    wide = {}
    for col in ("close", "volume"):
        wide[col] = px.pivot(index="timestamp", columns="symbol", values=col).sort_index().ffill()
    return wide


def generate_signals(context):
    """Return target weights for volume-confirmed price-pressure continuation.

    Signal definition:
    - Compute latest 3-session close-to-close return as short-horizon price pressure.
    - Confirm it with abnormal share volume and/or dollar volume using 60-session
      prior-window z-scores (shifted one bar to avoid including the signal bar in
      the baseline).
    - Score = signed recent return * average positive volume confirmation strength.
    - Gross-normalize to 1.0 and cap concentration; return zero until enough data.
    """
    output_symbols = list(context.symbols)
    symbols = [s for s in output_symbols if s in UNIVERSE]
    required_rows = PARAMS.volume_z_window + PARAMS.return_window + 2
    if len(symbols) < PARAMS.min_symbols or context.prices.empty:
        return _zero_weights(output_symbols)

    wide = _wide(context.prices, symbols)
    if wide is None:
        return _zero_weights(output_symbols)

    close = wide["close"].dropna(axis=1, how="any")
    volume = wide["volume"].reindex_like(close)
    tradable = [s for s in symbols if s in close.columns]
    if len(tradable) < PARAMS.min_symbols or len(close) < required_rows:
        return _zero_weights(output_symbols)

    close = close[tradable]
    volume = volume[tradable]
    dollar_volume = close * volume

    ret = close.pct_change(PARAMS.return_window)

    # Shift the rolling baseline one session so today's confirmation is judged
    # against only information known before the latest completed bar.
    vol_mean = volume.shift(1).rolling(PARAMS.volume_z_window, min_periods=PARAMS.volume_z_window).mean()
    vol_std = volume.shift(1).rolling(PARAMS.volume_z_window, min_periods=PARAMS.volume_z_window).std()
    dvol_mean = dollar_volume.shift(1).rolling(PARAMS.volume_z_window, min_periods=PARAMS.volume_z_window).mean()
    dvol_std = dollar_volume.shift(1).rolling(PARAMS.volume_z_window, min_periods=PARAMS.volume_z_window).std()

    vol_z = ((volume - vol_mean) / vol_std.replace(0.0, pd.NA)).replace([float("inf"), float("-inf")], pd.NA)
    dvol_z = ((dollar_volume - dvol_mean) / dvol_std.replace(0.0, pd.NA)).replace(
        [float("inf"), float("-inf")], pd.NA
    )

    latest = close.index[-1]
    raw = {s: 0.0 for s in output_symbols}
    for symbol in tradable:
        pressure = ret.loc[latest, symbol]
        vz = vol_z.loc[latest, symbol]
        dvz = dvol_z.loc[latest, symbol]
        if pd.isna(pressure) or pd.isna(vz) or pd.isna(dvz):
            continue
        if abs(float(pressure)) <= 0.0:
            continue

        share_confirm = max(0.0, float(vz) - PARAMS.volume_z_min)
        dollar_confirm = max(0.0, float(dvz) - PARAMS.dollar_volume_z_min)
        if share_confirm <= 0.0 and dollar_confirm <= 0.0:
            continue

        confirmation = 1.0 + 0.5 * (share_confirm + dollar_confirm)
        raw[symbol] = float(pressure) * confirmation

    return _cap_and_normalize(raw, PARAMS.max_abs_weight)
