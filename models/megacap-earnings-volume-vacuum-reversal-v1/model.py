"""AR-084 mega-cap post-earnings volume-vacuum reversal allocator.

QFA contract: expose generate_signals(context) -> dict[str, float].
Research-only model; uses only OHLCV bars supplied by qfa/Alpaca and never
places orders.

Important data caveat: qfa/Alpaca daily bars do not include a point-in-time
public earnings calendar. This model therefore uses a documented approximation:
"earnings-like" event bars are large abnormal-volume, large residual-return days.
The signal waits for subsequent low-volume/drought and failed follow-through
before taking the opposite direction for a short horizon, so it avoids using
future returns beyond the current completed bar but it is not a true verified
calendar-earnings strategy.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

UNIVERSE = ("AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "AVGO", "TSLA", "JPM", "LLY")


class ModelParams:
    # Search-default family from issue: event lookback [1,3], drought lookback [3,5], hold [3,5,10].
    event_lookback_days = (1, 2, 3)
    drought_lookbacks = (3, 5)
    hold_decay = (1.00, 0.80, 0.65, 0.50, 0.35)  # effective 5-session reversal hold
    volume_z_window = 63
    residual_z_window = 63
    volatility_window = 20
    beta_window = 60
    market_vol_window = 20
    market_vol_rank_window = 252
    min_history = 130
    min_symbols = 6
    event_volume_z = 1.10
    min_abs_event_residual = 0.012
    min_event_resid_z = 0.55
    max_drought_ratio = 0.83
    max_followthrough_same_direction = 0.006
    min_failure_ratio = -0.15
    high_market_vol_rank = 0.82
    high_market_vol_brake = 0.55
    max_abs_weight = 0.22
    beta_neutralize = True


PARAMS = ModelParams()


def _zero(symbols: list[str]) -> dict[str, float]:
    return {s: 0.0 for s in symbols}


def _wide(prices: pd.DataFrame, symbols: list[str]) -> dict[str, pd.DataFrame] | None:
    if prices is None or prices.empty:
        return None
    p = prices[prices["symbol"].isin(symbols)].copy()
    if p.empty:
        return None
    p["timestamp"] = pd.to_datetime(p["timestamp"], utc=True)
    out = {}
    for col in ("open", "high", "low", "close", "volume"):
        if col not in p.columns:
            return None
        out[col] = p.pivot(index="timestamp", columns="symbol", values=col).sort_index().ffill()
    return out


def _zscore(x: pd.DataFrame, window: int) -> pd.DataFrame:
    mean = x.shift(1).rolling(window, min_periods=window).mean()
    std = x.shift(1).rolling(window, min_periods=window).std(ddof=1)
    return ((x - mean) / std).replace([np.inf, -np.inf], np.nan)


def _normalize(raw: dict[str, float], symbols: list[str], beta: pd.Series | None = None) -> dict[str, float]:
    vals = pd.Series({s: float(raw.get(s, 0.0)) for s in symbols}, dtype=float).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    if vals.abs().sum() <= 0:
        return _zero(symbols)
    # Remove common cross-sectional bias; then optionally neutralize estimated market beta.
    vals = vals - vals.mean()
    if PARAMS.beta_neutralize and beta is not None:
        b = beta.reindex(vals.index).replace([np.inf, -np.inf], np.nan).fillna(1.0)
        denom = float((b * b).sum())
        if denom > 1e-12:
            vals = vals - b * float((vals * b).sum() / denom)
    vals = vals.where(vals.abs() >= 1e-12, 0.0)
    if vals.abs().sum() <= 0:
        return _zero(symbols)
    vals = vals / vals.abs().sum()
    vals = vals.clip(lower=-PARAMS.max_abs_weight, upper=PARAMS.max_abs_weight)
    gross = float(vals.abs().sum())
    if gross <= 0:
        return _zero(symbols)
    vals = vals / gross
    return {s: float(vals.get(s, 0.0)) for s in symbols}


def generate_signals(context) -> dict[str, float]:
    """Return next-bar target weights for event-volume-vacuum reversals."""
    output_symbols = list(getattr(context, "symbols", []) or [])
    symbols = [s for s in output_symbols if s in UNIVERSE]
    if len(symbols) < PARAMS.min_symbols:
        return _zero(output_symbols)
    wide = _wide(getattr(context, "prices", pd.DataFrame()), symbols)
    if wide is None:
        return _zero(output_symbols)

    close = wide["close"][symbols].dropna(axis=1, how="any")
    tradable = [s for s in symbols if s in close.columns]
    if len(tradable) < PARAMS.min_symbols or len(close) < PARAMS.min_history:
        return _zero(output_symbols)
    close = close[tradable]
    volume = wide["volume"][tradable]

    p = PARAMS
    ret = close.pct_change().replace([np.inf, -np.inf], np.nan)
    market_ret = ret.mean(axis=1)
    residual_ret = ret.sub(market_ret, axis=0)
    residual_z = _zscore(residual_ret, p.residual_z_window)
    log_vol = np.log(volume.where(volume > 0))
    volume_z = _zscore(log_vol, p.volume_z_window)
    median_volume = volume.shift(1).rolling(p.volume_z_window, min_periods=p.volume_z_window).median()
    vol = ret.shift(1).rolling(p.volatility_window, min_periods=p.volatility_window).std(ddof=1)
    inv_vol = (1.0 / vol).replace([np.inf, -np.inf], np.nan)
    inv_vol = inv_vol.div(inv_vol.median(axis=1), axis=0).clip(lower=0.55, upper=1.80).fillna(1.0)

    # Market beta brake/neutralizer estimated only from completed bars.
    cov = ret.rolling(p.beta_window, min_periods=p.beta_window).cov(market_ret)
    var = market_ret.rolling(p.beta_window, min_periods=p.beta_window).var(ddof=1)
    beta = (cov.iloc[-1] / float(var.iloc[-1])) if len(var) and pd.notna(var.iloc[-1]) and float(var.iloc[-1]) > 0 else pd.Series(1.0, index=tradable)
    market_vol = market_ret.rolling(p.market_vol_window, min_periods=p.market_vol_window).std(ddof=1)
    market_vol_rank = market_vol.rolling(p.market_vol_rank_window, min_periods=60).rank(pct=True)
    brake = p.high_market_vol_brake if len(market_vol_rank) and pd.notna(market_vol_rank.iloc[-1]) and float(market_vol_rank.iloc[-1]) > p.high_market_vol_rank else 1.0

    raw = {s: 0.0 for s in output_symbols}
    n = len(close)
    # Score recent event bars that are followed by drought and failure as of now.
    for hold_age, hold_decay in enumerate(p.hold_decay):
        asof_offset = hold_age
        now_pos = n - 1 - asof_offset
        if now_pos <= p.volume_z_window + max(p.drought_lookbacks):
            continue
        for event_age in p.event_lookback_days:
            event_pos = now_pos - event_age
            if event_pos <= 0:
                continue
            event_ts = close.index[event_pos]
            now_ts = close.index[now_pos]
            for s in tradable:
                ev_ret = residual_ret.loc[event_ts, s]
                ev_z = residual_z.loc[event_ts, s]
                ev_vz = volume_z.loc[event_ts, s]
                if pd.isna(ev_ret) or pd.isna(ev_z) or pd.isna(ev_vz):
                    continue
                if float(ev_vz) < p.event_volume_z or abs(float(ev_ret)) < p.min_abs_event_residual or abs(float(ev_z)) < p.min_event_resid_z:
                    continue
                direction = -1.0 if float(ev_ret) > 0 else 1.0
                drought_scores: list[float] = []
                for dwin in p.drought_lookbacks:
                    start = max(event_pos + 1, now_pos - dwin + 1)
                    if start > now_pos:
                        continue
                    recent_vol = volume[s].iloc[start:now_pos + 1].mean()
                    base_vol = median_volume.loc[event_ts, s]
                    if pd.notna(recent_vol) and pd.notna(base_vol) and float(base_vol) > 0:
                        drought_scores.append(float(recent_vol / base_vol))
                if not drought_scores:
                    continue
                drought_ratio = min(drought_scores)
                if drought_ratio > p.max_drought_ratio:
                    continue
                follow = float((close.loc[now_ts, s] / close.loc[event_ts, s]) - 1.0)
                same_direction_follow = follow if float(ev_ret) > 0 else -follow
                failure_ratio = same_direction_follow / max(abs(float(ev_ret)), 1e-9)
                if same_direction_follow > p.max_followthrough_same_direction or failure_ratio > p.min_failure_ratio:
                    continue
                drought_bonus = max(0.0, p.max_drought_ratio - drought_ratio) / p.max_drought_ratio
                fail_bonus = min(2.0, max(0.0, -failure_ratio))
                vol_scale = float(inv_vol.loc[now_ts, s]) if now_ts in inv_vol.index and pd.notna(inv_vol.loc[now_ts, s]) else 1.0
                strength = (abs(float(ev_z)) + 0.25 * max(float(ev_vz) - p.event_volume_z, 0.0)) * (1.0 + drought_bonus + 0.35 * fail_bonus)
                raw[s] += direction * hold_decay * strength * vol_scale * brake

    return _normalize(raw, output_symbols, beta=beta)
