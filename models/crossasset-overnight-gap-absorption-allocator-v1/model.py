"""AR-089 cross-asset ETF overnight gap absorption allocator.

QFA contract: expose generate_signals(context) -> dict[str, float].
Uses only OHLCV bars supplied by qfa/Alpaca; no CSV input, no daemon, no orders.

Mechanism: use yesterday's close-to-today-open overnight gap and today's
open-to-close absorption/reversal to allocate for the next session across equity,
duration, gold, credit, and defensive sector ETFs. Daily bars cannot trade the
same open after observing that open; therefore this implementation is strictly
point-in-time at the current bar close and targets the next session.
"""
from __future__ import annotations

from typing import Any, NamedTuple

import numpy as np
import pandas as pd

UNIVERSE = ("SPY", "QQQ", "IWM", "TLT", "IEF", "GLD", "HYG", "LQD", "SHY", "XLE", "XLU", "XLV")
RISK = ("SPY", "QQQ", "IWM", "XLE", "XLV", "HYG")
DEFENSIVE = ("TLT", "IEF", "GLD", "LQD", "SHY", "XLU")
DURATION = ("TLT", "IEF")
CREDIT = ("HYG", "LQD")


class Params(NamedTuple):
    lookback: int = 60
    min_history: int = 45
    gap_z_threshold: float = 1.0
    absorption_z_threshold: float = 0.25
    dispersion_min: float = 0.003
    max_gross: float = 1.0
    max_single: float = 0.35
    vol_target_daily: float = 0.008
    min_active: int = 3
    confirmation_tilt: float = 0.25


PARAMS = Params()


def _flat(symbols: list[str]) -> dict[str, float]:
    return {s: 0.0 for s in symbols}


def _normalize(raw: dict[str, float], symbols: list[str], max_gross: float, max_single: float) -> dict[str, float]:
    vals = pd.Series({s: float(raw.get(s, 0.0)) for s in symbols}, dtype=float)
    vals = vals.replace([np.inf, -np.inf], np.nan).fillna(0.0).clip(-max_single, max_single)
    gross = float(vals.abs().sum())
    if gross <= 0:
        return _flat(symbols)
    if gross > max_gross:
        vals *= max_gross / gross
    return {s: float(vals.get(s, 0.0)) for s in symbols}


def _daily_panel(prices: pd.DataFrame, symbols: list[str], as_of: pd.Timestamp) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame] | None:
    df = prices[prices["symbol"].isin(symbols)].copy()
    if df.empty:
        return None
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df[df["timestamp"] <= as_of].sort_values(["timestamp", "symbol"])
    if df.empty:
        return None
    close = df.pivot(index="timestamp", columns="symbol", values="close").ffill()
    open_ = df.pivot(index="timestamp", columns="symbol", values="open").ffill()
    volume = df.pivot(index="timestamp", columns="symbol", values="volume").ffill()
    keep = [s for s in symbols if s in close.columns and s in open_.columns]
    close, open_, volume = close[keep].dropna(how="all"), open_[keep].dropna(how="all"), volume[keep].dropna(how="all")
    if len(close) < PARAMS.min_history + 2:
        return None
    return open_, close, volume


def _scores(prices: pd.DataFrame, symbols: list[str], as_of: pd.Timestamp, p: Params = PARAMS) -> pd.Series | None:
    panel = _daily_panel(prices, symbols, as_of)
    if panel is None:
        return None
    open_, close, _volume = panel
    common_idx = close.index.intersection(open_.index)
    open_, close = open_.loc[common_idx], close.loc[common_idx]
    prev_close = close.shift(1)
    gap = open_ / prev_close - 1.0
    open_to_close = close / open_ - 1.0
    cc_ret = close.pct_change()

    hist_gap = gap.iloc[-p.lookback - 1 : -1]
    hist_oc = open_to_close.iloc[-p.lookback - 1 : -1]
    if len(hist_gap) < p.min_history:
        return None
    latest_gap = gap.iloc[-1]
    latest_oc = open_to_close.iloc[-1]
    gap_z = (latest_gap - hist_gap.mean()) / hist_gap.std(ddof=1).replace(0.0, np.nan)
    oc_z = (latest_oc - hist_oc.mean()) / hist_oc.std(ddof=1).replace(0.0, np.nan)

    dispersion = float(latest_gap.dropna().std(ddof=1)) if latest_gap.notna().sum() > 2 else 0.0
    if not np.isfinite(dispersion) or dispersion < p.dispersion_min:
        return None

    # Positive score: gap down then upward absorption; negative: gap up then downward absorption.
    reversal_strength = -gap_z * oc_z.abs() * np.sign(oc_z)
    valid = (gap_z.abs() >= p.gap_z_threshold) & (oc_z.abs() >= p.absorption_z_threshold) & (np.sign(latest_gap) == -np.sign(latest_oc))
    scores = reversal_strength.where(valid, 0.0).replace([np.inf, -np.inf], np.nan).fillna(0.0)

    # Cross-asset confirmation: credit absorption better than duration favors risk sleeves;
    # duration better than credit favors defensive sleeves. This changes sizing, not direction.
    credit_score = float(scores.reindex([s for s in CREDIT if s in scores.index]).mean()) if any(s in scores.index for s in CREDIT) else 0.0
    duration_score = float(scores.reindex([s for s in DURATION if s in scores.index]).mean()) if any(s in scores.index for s in DURATION) else 0.0
    confirm = np.tanh((credit_score - duration_score) / 2.0) if np.isfinite(credit_score - duration_score) else 0.0
    for s in scores.index:
        if s in RISK:
            scores.loc[s] *= 1.0 + p.confirmation_tilt * confirm
        elif s in DEFENSIVE:
            scores.loc[s] *= 1.0 - p.confirmation_tilt * confirm

    # Volatility scaler: downweight high realized-vol symbols.
    vol = cc_ret.iloc[-p.lookback:].std(ddof=1) * np.sqrt(1.0)
    scaler = (p.vol_target_daily / vol.replace(0.0, np.nan)).clip(0.25, 1.5)
    scores = (scores * scaler).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    if int((scores.abs() > 0).sum()) < p.min_active:
        return None
    return scores


def generate_signals(context: Any) -> dict[str, float]:
    symbols_out = list(getattr(context, "symbols", []) or [])
    weights = _flat(symbols_out)
    symbols = [s for s in symbols_out if s in UNIVERSE]
    prices = getattr(context, "prices", None)
    as_of_raw = getattr(context, "as_of", None)
    if not symbols or prices is None or getattr(prices, "empty", True) or as_of_raw is None:
        return weights
    try:
        as_of = pd.Timestamp(as_of_raw)
        as_of = as_of.tz_localize("UTC") if as_of.tzinfo is None else as_of.tz_convert("UTC")
    except Exception:
        return weights
    scores = _scores(prices, symbols, as_of, PARAMS)
    if scores is None or scores.abs().sum() <= 0:
        return weights
    active = scores[scores.abs() > 0].sort_values(key=lambda x: x.abs(), ascending=False).head(8)
    denom = float(active.abs().sum())
    if denom <= 0:
        return weights
    raw = {s: 0.0 for s in symbols_out}
    for s, score in active.items():
        raw[s] = float(score) / denom
    return _normalize(raw, symbols_out, PARAMS.max_gross, PARAMS.max_single)
