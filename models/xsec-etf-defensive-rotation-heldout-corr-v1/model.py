"""Held-out-correlation-target ETF defensive rotation alpha (AR-062).

QFA contract: expose generate_signals(context) -> dict[str, float].
The model is research-only and consumes only context.prices OHLCV bars.  It
starts from AR-051's liquid ETF defensive rotation universe, but replaces the
single in-model proxy brake with explicit score penalties against two
pre-declared held-out proxy streams: a TSMOM-like risk trend stream and a
carry/defensive stream.  The target is to preserve monthly momentum/volatility
rotation while reducing redundancy to retained alpha curves.
"""

from __future__ import annotations

import math

import pandas as pd

DEFAULT_PARAMS = {
    "momentum_lookback": 126,
    "secondary_lookback": 63,
    "vol_window": 63,
    "corr_window": 126,
    "min_periods": 210,
    "top_n": 3,
    "corr_target": 0.35,
    "corr_penalty": 1.10,
    "target_vol": 0.09,
    "max_abs_weight": 0.40,
    "min_defensive_weight": 0.35,
    "risk_on_symbols": ("SPY", "QQQ", "IWM", "XLV", "XLY", "XLE"),
    "defensive_symbols": ("XLU", "XLP", "TLT", "IEF", "GLD", "SHY"),
    "heldout_tsmom_proxy_symbols": ("SPY", "QQQ", "IWM", "TLT", "GLD"),
    "heldout_carry_defensive_proxy_symbols": ("IEF", "TLT", "GLD", "XLP", "XLU", "SHY"),
}


def _params(context) -> dict:
    metadata = getattr(context, "metadata", {}) or {}
    provided = metadata.get("params", {}) if isinstance(metadata, dict) else {}
    params = DEFAULT_PARAMS.copy()
    params.update({k: provided[k] for k in params.keys() & provided.keys()})
    return params


def _gross_normalize(weights: dict[str, float]) -> dict[str, float]:
    gross = sum(abs(v) for v in weights.values())
    if gross <= 0:
        return {symbol: 0.0 for symbol in weights}
    return {symbol: float(v / gross) for symbol, v in weights.items()}


def _cap_and_renormalize(weights: dict[str, float], cap: float) -> dict[str, float]:
    if not weights:
        return {}
    capped = {symbol: max(min(float(value), cap), -cap) for symbol, value in weights.items()}
    return _gross_normalize(capped)


def _monthly_decision_frame(close: pd.DataFrame, as_of: pd.Timestamp) -> pd.DataFrame:
    if close.empty:
        return close
    as_of = pd.Timestamp(as_of)
    month_start = pd.Timestamp(year=as_of.year, month=as_of.month, day=1, tz=as_of.tz)
    prior = close[close.index < month_start]
    if len(prior) >= 2:
        return prior
    return close[close.index <= as_of]


def _heldout_streams(returns: pd.DataFrame, params: dict) -> list[pd.Series]:
    streams: list[pd.Series] = []
    specs = (
        ("heldout_tsmom_proxy_symbols", {"SPY": 0.30, "QQQ": 0.25, "IWM": 0.15, "TLT": 0.15, "GLD": 0.15}),
        ("heldout_carry_defensive_proxy_symbols", {"IEF": 0.25, "TLT": 0.25, "GLD": 0.20, "XLP": 0.15, "XLU": 0.10, "SHY": 0.05}),
    )
    for key, default_weights in specs:
        members = [s for s in params[key] if s in returns.columns]
        if not members:
            continue
        weights = pd.Series({s: default_weights.get(s, 1.0) for s in members}, dtype=float)
        weights = weights / weights.abs().sum()
        streams.append(returns[members].mul(weights, axis=1).sum(axis=1))
    return streams


def _excess_heldout_corr(returns: pd.DataFrame, symbols: list[str], params: dict) -> pd.Series:
    tail = returns.tail(int(params["corr_window"])).dropna(how="all")
    if len(tail) < 40:
        return pd.Series(0.0, index=symbols)
    streams = _heldout_streams(tail, params)
    if not streams:
        return pd.Series(0.0, index=symbols)
    target = float(params["corr_target"])
    penalties: dict[str, float] = {}
    for symbol in symbols:
        if symbol not in tail.columns:
            penalties[symbol] = 0.0
            continue
        corrs = []
        for stream in streams:
            corr = tail[symbol].corr(stream)
            if pd.notna(corr):
                corrs.append(abs(float(corr)))
        penalties[symbol] = max(0.0, max(corrs) - target) if corrs else 0.0
    return pd.Series(penalties)


def _ensure_defensive_floor(raw: dict[str, float], score: pd.Series, inv_vol: pd.Series, params: dict) -> dict[str, float]:
    defensive = [s for s in params["defensive_symbols"] if s in score.index]
    if not defensive:
        return raw
    floor = float(params["min_defensive_weight"])
    current_def = sum(max(0.0, raw.get(s, 0.0)) for s in defensive)
    total = sum(max(0.0, v) for v in raw.values())
    if total > 0 and current_def / total >= floor:
        return raw
    defensive_rank = (score.reindex(defensive).fillna(-999.0) + 0.10 * inv_vol.reindex(defensive).fillna(0.0)).sort_values(ascending=False)
    add_symbol = str(defensive_rank.index[0])
    raw[add_symbol] = raw.get(add_symbol, 0.0) + max(0.05, floor)
    return raw


def generate_signals(context):
    """Return monthly long-only ETF weights capped at gross exposure 1.0.

    Uses prior month-end data, blended 63/126-day momentum over realized vol,
    explicit held-out correlation target penalties, and a defensive sleeve floor
    to test lower redundancy versus AR-051 / TSMOM / carry-defensive curves.
    """
    symbols = list(getattr(context, "symbols", []) or [])
    if not symbols:
        return {}
    params = _params(context)
    prices = getattr(context, "prices", pd.DataFrame()).copy()
    required = {"timestamp", "symbol", "close"}
    if prices.empty or not required.issubset(prices.columns):
        return {symbol: 0.0 for symbol in symbols}

    prices["timestamp"] = pd.to_datetime(prices["timestamp"], utc=True)
    close = (
        prices[prices["symbol"].isin(symbols)]
        .pivot(index="timestamp", columns="symbol", values="close")
        .sort_index()
        .ffill()
    )
    close = close.reindex(columns=symbols).dropna(how="all")
    if close.empty:
        return {symbol: 0.0 for symbol in symbols}
    as_of = pd.Timestamp(getattr(context, "as_of", close.index[-1]))
    decision_close = _monthly_decision_frame(close, as_of).dropna(how="all")
    if len(decision_close) < int(params["min_periods"]):
        return {symbol: 0.0 for symbol in symbols}

    long_lb = min(int(params["momentum_lookback"]), len(decision_close) - 1)
    short_lb = min(int(params["secondary_lookback"]), len(decision_close) - 1)
    vol_window = min(int(params["vol_window"]), len(decision_close) - 1)
    if min(long_lb, short_lb, vol_window) < 20:
        return {symbol: 0.0 for symbol in symbols}

    returns = decision_close.pct_change()
    ret_long = decision_close.iloc[-1] / decision_close.iloc[-1 - long_lb] - 1.0
    ret_short = decision_close.iloc[-1] / decision_close.iloc[-1 - short_lb] - 1.0
    realized_vol = (returns.tail(vol_window).std(ddof=1) * math.sqrt(252)).replace(0.0, pd.NA)
    realized_vol = realized_vol.fillna(float(params["target_vol"])).clip(lower=0.04)
    inv_vol = (float(params["target_vol"]) / realized_vol).clip(upper=3.0)

    blended_momentum = 0.60 * ret_long + 0.40 * ret_short
    raw_score = (blended_momentum / realized_vol).replace([float("inf"), float("-inf")], pd.NA)
    penalty = _excess_heldout_corr(returns, symbols, params)
    score = (raw_score - float(params["corr_penalty"]) * penalty).dropna()

    risk_on = [s for s in params["risk_on_symbols"] if s in symbols and s in score.index]
    defensive = [s for s in params["defensive_symbols"] if s in symbols and s in score.index]
    weights = {symbol: 0.0 for symbol in symbols}
    if not risk_on or not defensive:
        return weights

    risk_on_median = float(score.reindex(risk_on).dropna().median())
    defensive_median = float(score.reindex(defensive).dropna().median())
    spy_momentum = float(blended_momentum.get("SPY", 0.0) or 0.0)
    if risk_on_median > defensive_median and spy_momentum > 0.0:
        candidate_symbols = risk_on + defensive
    else:
        candidate_symbols = defensive + [s for s in risk_on if s in ("XLV", "SPY")]

    ranked = score.reindex(candidate_symbols).dropna().sort_values(ascending=False)
    selected = list(dict.fromkeys(ranked.head(max(1, int(params["top_n"]))).index))
    if not selected:
        selected = candidate_symbols[: max(1, int(params["top_n"]))]

    raw: dict[str, float] = {}
    for symbol in selected:
        positive_score = max(float(score.get(symbol, 0.0) or 0.0), 0.0)
        raw[symbol] = (positive_score + 0.01) * float(inv_vol.get(symbol, 1.0) or 1.0)
    if sum(abs(v) for v in raw.values()) <= 0.0:
        raw = {symbol: 1.0 for symbol in selected}
    raw = _ensure_defensive_floor(raw, score, inv_vol, params)
    weights.update(_cap_and_renormalize(raw, float(params["max_abs_weight"])))
    return weights
