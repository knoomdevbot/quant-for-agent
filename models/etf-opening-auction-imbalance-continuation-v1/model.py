"""AR-087 ETF opening-auction / early-session VWAP imbalance continuation.

QFA-compatible research alpha exposing generate_signals(context) -> dict[str, float].
Uses only OHLCV bars supplied by qfa/Alpaca; no CSV input, no daemon, no orders.

Mechanism: after the first regular-session 30 minutes, measure each ETF's opening
range return, deviation from early VWAP, and relative volume versus recent first-30
minute history.  If broad risk/defensive breadth confirms a directional opening
imbalance, hold a capped continuation basket for a short intraday window.
"""
from __future__ import annotations

import math
import numpy as np
import pandas as pd

UNIVERSE = ("SPY", "QQQ", "IWM", "XLV", "XLY", "XLE", "XLU", "XLP", "TLT", "IEF", "GLD", "HYG", "LQD", "SHY")
RISK = ("SPY", "QQQ", "IWM", "XLV", "XLY", "XLE", "HYG")
DEFENSIVE = ("TLT", "IEF", "GLD", "LQD", "SHY", "XLU", "XLP")


class Params:
    opening_minutes = 30
    min_days_history = 20
    max_days_history = 45
    entry_delay_minutes = 1
    hold_minutes = 120
    imbalance_z = 1.0
    vwap_dev_z = 0.75
    rel_volume_min = 0.80
    breadth_min_abs = 0.20
    min_active_symbols = 6
    max_gross = 1.0
    max_single = 0.16


PARAMS = Params()


def _flat(symbols) -> dict[str, float]:
    return {s: 0.0 for s in symbols}


def _to_utc(ts) -> pd.Timestamp | None:
    try:
        out = pd.Timestamp(ts)
    except Exception:
        return None
    if out.tzinfo is None:
        return out.tz_localize("UTC")
    return out.tz_convert("UTC")


def _session_open_utc(as_of: pd.Timestamp) -> pd.Timestamp:
    # NYSE regular open is 09:30 America/New_York; timezone conversion handles DST.
    ny = as_of.tz_convert("America/New_York")
    return pd.Timestamp(year=ny.year, month=ny.month, day=ny.day, hour=9, minute=30, tz="America/New_York").tz_convert("UTC")


def _in_regular_session(as_of: pd.Timestamp) -> bool:
    ny = as_of.tz_convert("America/New_York")
    minutes = ny.hour * 60 + ny.minute
    return ny.weekday() < 5 and (9 * 60 + 30) <= minutes <= (16 * 60)


def _normalize(raw: dict[str, float], symbols: list[str], max_gross: float, max_single: float) -> dict[str, float]:
    vals = pd.Series({s: float(raw.get(s, 0.0)) for s in symbols}, dtype=float).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    vals = vals.clip(lower=-max_single, upper=max_single)
    gross = float(vals.abs().sum())
    if gross <= 0:
        return _flat(symbols)
    if gross > max_gross:
        vals *= max_gross / gross
    return {s: float(vals.get(s, 0.0)) for s in symbols}


def _opening_features(df: pd.DataFrame, symbols: list[str], as_of: pd.Timestamp, p: Params):
    df = df[df["symbol"].isin(symbols)].copy()
    if df.empty:
        return None
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df[df["timestamp"] <= as_of].sort_values(["timestamp", "symbol"])
    if df.empty:
        return None

    session_open = _session_open_utc(as_of)
    entry_start = session_open + pd.Timedelta(minutes=p.opening_minutes + p.entry_delay_minutes)
    exit_time = entry_start + pd.Timedelta(minutes=p.hold_minutes)
    if as_of < entry_start or as_of > exit_time:
        return None

    # Limit to recent sessions for speed and point-in-time history.
    start_tail = session_open - pd.Timedelta(days=p.max_days_history * 2 + 10)
    df = df[df["timestamp"] >= start_tail]
    df["session"] = df["timestamp"].dt.tz_convert("America/New_York").dt.date
    df["session_open"] = pd.to_datetime(df["session"].astype(str) + " 09:30:00").dt.tz_localize("America/New_York").dt.tz_convert("UTC")
    df["minute_from_open"] = ((df["timestamp"] - df["session_open"]).dt.total_seconds() // 60).astype(int)
    first = df[(df["minute_from_open"] >= 0) & (df["minute_from_open"] < p.opening_minutes)].copy()
    if first.empty:
        return None
    first["pv"] = first["close"] * first["volume"].clip(lower=0)
    grouped = first.groupby(["session", "symbol"])
    feat = grouped.agg(open_px=("open", "first"), close_px=("close", "last"), vol=("volume", "sum"), pv=("pv", "sum")).reset_index()
    feat["open_ret"] = feat["close_px"] / feat["open_px"] - 1.0
    feat["vwap"] = feat["pv"] / feat["vol"].replace(0.0, np.nan)
    feat["vwap_dev"] = feat["close_px"] / feat["vwap"] - 1.0
    current_session = as_of.tz_convert("America/New_York").date()
    cur = feat[feat["session"] == current_session].set_index("symbol")
    hist = feat[feat["session"] < current_session]
    if cur.empty or len(hist["session"].unique()) < p.min_days_history:
        return None
    hist = hist.sort_values("session").groupby("symbol").tail(p.max_days_history)
    stats = hist.groupby("symbol").agg(ret_mu=("open_ret", "mean"), ret_sd=("open_ret", "std"), dev_mu=("vwap_dev", "mean"), dev_sd=("vwap_dev", "std"), vol_med=("vol", "median"))
    joined = cur.join(stats, how="inner")
    if len(joined) < p.min_active_symbols:
        return None
    joined["ret_z"] = (joined["open_ret"] - joined["ret_mu"]) / joined["ret_sd"].replace(0.0, np.nan)
    joined["dev_z"] = (joined["vwap_dev"] - joined["dev_mu"]) / joined["dev_sd"].replace(0.0, np.nan)
    joined["rel_vol"] = joined["vol"] / joined["vol_med"].replace(0.0, np.nan)
    joined = joined.replace([np.inf, -np.inf], np.nan).dropna(subset=["ret_z", "dev_z", "rel_vol"])
    return joined


def generate_signals(context) -> dict[str, float]:
    symbols_out = list(getattr(context, "symbols", []) or [])
    weights = _flat(symbols_out)
    symbols = [s for s in symbols_out if s in UNIVERSE]
    as_of = _to_utc(getattr(context, "as_of", None))
    prices = getattr(context, "prices", None)
    if as_of is None or prices is None or getattr(prices, "empty", True) or not _in_regular_session(as_of):
        return weights
    feat = _opening_features(prices, symbols, as_of, PARAMS)
    if feat is None or feat.empty:
        return weights
    p = PARAMS
    active = feat[feat["rel_vol"] >= p.rel_volume_min].copy()
    if len(active) < p.min_active_symbols:
        return weights
    long_mask = (active["ret_z"] >= p.imbalance_z) & (active["dev_z"] >= p.vwap_dev_z)
    short_mask = (active["ret_z"] <= -p.imbalance_z) & (active["dev_z"] <= -p.vwap_dev_z)
    directional = pd.Series(0.0, index=active.index)
    directional.loc[long_mask] = 1.0
    directional.loc[short_mask] = -1.0
    if directional.abs().sum() < p.min_active_symbols / 3:
        return weights
    risk_names = [s for s in active.index if s in RISK]
    def_names = [s for s in active.index if s in DEFENSIVE]
    risk_breadth = float(directional.reindex(risk_names).mean()) if risk_names else 0.0
    def_breadth = float(directional.reindex(def_names).mean()) if def_names else 0.0
    # Continuation when risk and defensive/quality sleeves are not strongly offsetting.
    net_breadth = 0.75 * risk_breadth + 0.25 * def_breadth
    if not math.isfinite(net_breadth) or abs(net_breadth) < p.breadth_min_abs:
        return weights
    raw = {s: 0.0 for s in symbols_out}
    strength = min(1.0, abs(net_breadth) / 0.60)
    signed_scores = (0.65 * active["ret_z"].clip(-3, 3) + 0.35 * active["dev_z"].clip(-3, 3)) * active["rel_vol"].clip(0.5, 2.0)
    if net_breadth > 0:
        candidates = signed_scores[signed_scores > 0].sort_values(ascending=False).head(8)
        denom = float(candidates.abs().sum())
        if denom <= 0:
            return weights
        for s, score in candidates.items():
            raw[s] = strength * float(score) / denom
    else:
        candidates = signed_scores[signed_scores < 0].sort_values(ascending=True).head(8)
        denom = float(candidates.abs().sum())
        if denom <= 0:
            return weights
        for s, score in candidates.items():
            raw[s] = strength * float(score) / denom
    return _normalize(raw, symbols_out, p.max_gross, p.max_single)
