"""Event-liquidity overnight gap reversal alpha for mega-cap equities.

QFA contract: expose generate_signals(context) -> dict[symbol, weight].
Research-only model; it never places orders.

Mechanism: overnight gaps paired with unusual volume/range are treated as
news/liquidity-shock events that can over-dislocate opening prices. The intended
economic trade is contrarian open-to-close on the event day. qfa daily backtests
call generate_signals only after the latest completed daily bar and apply weights
to the next close-to-close return, so this qfa model is a lagged compatibility
proxy. The evaluation artifacts also include a direct Alpaca OHLC harness for the
intended same-day open-to-close path.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

UNIVERSE = ("AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA")


class ModelParams:
    gap_z_window = 60
    volume_z_window = 60
    atr_window = 20
    entry_gap_z = 1.25
    event_volume_z = 0.75
    event_range_atr = 0.80
    max_abs_weight = 0.25
    min_symbols = 3


PARAMS = ModelParams()


def _zero_weights(symbols):
    return {symbol: 0.0 for symbol in symbols}


def _cap_and_normalize(weights: dict[str, float], max_abs_weight: float) -> dict[str, float]:
    clean = {s: float(w) for s, w in weights.items() if math.isfinite(float(w))}
    gross = sum(abs(w) for w in clean.values())
    if not clean or gross <= 0.0:
        return {s: 0.0 for s in weights}
    scaled = {s: w / gross for s, w in clean.items()}
    capped = {s: max(-max_abs_weight, min(max_abs_weight, w)) for s, w in scaled.items()}
    capped_gross = sum(abs(w) for w in capped.values())
    if capped_gross <= 0.0:
        return {s: 0.0 for s in weights}
    return {s: float(capped.get(s, 0.0) / capped_gross) for s in weights}


def _wide(prices: pd.DataFrame, symbols: list[str]):
    px = prices[prices["symbol"].isin(symbols)].copy()
    if px.empty:
        return None
    px["timestamp"] = pd.to_datetime(px["timestamp"], utc=True)
    wide = {}
    for col in ("open", "high", "low", "close", "volume"):
        wide[col] = px.pivot(index="timestamp", columns="symbol", values=col).sort_index().ffill()
    return wide


def generate_signals(context):
    """Return contrarian target weights after event-like overnight gaps.

    Latest completed daily bar features:
    - overnight gap = open / prior close - 1, z-scored using prior-only history;
    - volume shock = log(volume) z-score using prior-only history;
    - range shock = high-low divided by prior ATR proxy.

    Trade rule:
    - only trade large gap events that also show abnormal volume or range;
    - fade the gap direction: positive gap -> short, negative gap -> long;
    - score by gap-z excess times a liquidity/event multiplier;
    - gross-normalize and cap single-name absolute weight.

    qfa limitation: daily qfa applies this signal to the *next* close-to-close
    return. It is therefore a durable qfa-compatible proxy for an intended
    same-session open-to-close event-liquidity reversal, which is evaluated
    separately in latest.json with Alpaca OHLC bars.
    """
    output_symbols = list(context.symbols)
    symbols = [s for s in output_symbols if s in UNIVERSE]
    if len(symbols) < PARAMS.min_symbols or context.prices.empty:
        return _zero_weights(output_symbols)

    wide = _wide(context.prices, symbols)
    if wide is None:
        return _zero_weights(output_symbols)

    open_ = wide["open"].dropna(axis=1, how="any")
    tradable = [s for s in symbols if s in open_.columns]
    required = max(PARAMS.gap_z_window, PARAMS.volume_z_window, PARAMS.atr_window) + 2
    if len(tradable) < PARAMS.min_symbols or len(open_) < required:
        return _zero_weights(output_symbols)

    open_ = wide["open"][tradable]
    high = wide["high"][tradable]
    low = wide["low"][tradable]
    close = wide["close"][tradable]
    volume = wide["volume"][tradable]

    gap = (open_ / close.shift(1) - 1.0).replace([float("inf"), float("-inf")], pd.NA)
    gap_mean = gap.shift(1).rolling(PARAMS.gap_z_window, min_periods=PARAMS.gap_z_window).mean()
    gap_std = gap.shift(1).rolling(PARAMS.gap_z_window, min_periods=PARAMS.gap_z_window).std()
    gap_z = ((gap - gap_mean) / gap_std).replace([float("inf"), float("-inf")], pd.NA)

    log_vol = np.log(volume.where(volume > 0))
    vol_mean = log_vol.shift(1).rolling(PARAMS.volume_z_window, min_periods=PARAMS.volume_z_window).mean()
    vol_std = log_vol.shift(1).rolling(PARAMS.volume_z_window, min_periods=PARAMS.volume_z_window).std()
    vol_z = ((log_vol - vol_mean) / vol_std).replace([float("inf"), float("-inf")], pd.NA)

    true_range = pd.concat(
        [(high - low).abs(), (high - close.shift(1)).abs(), (low - close.shift(1)).abs()],
        axis=0,
    ).groupby(level=0).max().sort_index()
    atr = true_range.shift(1).rolling(PARAMS.atr_window, min_periods=PARAMS.atr_window).mean()
    range_ratio = ((high - low).abs() / atr).replace([float("inf"), float("-inf")], pd.NA)

    latest = gap_z.index[-1]
    raw = {s: 0.0 for s in output_symbols}
    for symbol in tradable:
        gz = gap_z.loc[latest, symbol]
        vz = vol_z.loc[latest, symbol]
        rr = range_ratio.loc[latest, symbol]
        if pd.isna(gz):
            continue
        gz = float(gz)
        vz = 0.0 if pd.isna(vz) else float(vz)
        rr = 0.0 if pd.isna(rr) else float(rr)
        if abs(gz) < PARAMS.entry_gap_z:
            continue
        if vz < PARAMS.event_volume_z and rr < PARAMS.event_range_atr:
            continue
        event_multiplier = 1.0 + max(0.0, vz - PARAMS.event_volume_z) * 0.25 + max(0.0, rr - PARAMS.event_range_atr) * 0.10
        raw[symbol] = -math.copysign((abs(gz) - PARAMS.entry_gap_z) * event_multiplier, gz)

    return _cap_and_normalize(raw, PARAMS.max_abs_weight)
