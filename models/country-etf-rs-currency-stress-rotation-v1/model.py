from __future__ import annotations

import math
import numpy as np
import pandas as pd

COUNTRY_SYMBOLS = ["EFA", "EEM", "EWJ", "EWU", "EWG", "EWQ", "EWL", "EWC", "EWA", "EWH", "EWT", "EWS", "EWY", "EWW", "INDA", "FXI", "MCHI", "EWZ", "EZA"]
CONTEXT_SYMBOLS = ["UUP", "GLD", "DBC", "SPY"]
EXPORTERS = {"EWC", "EWA", "EWZ", "EZA"}
ASIA_IMPORTERS = {"EWJ", "EWH", "EWT", "EWS", "EWY", "FXI", "MCHI", "INDA"}


def generate_signals(context):
    """Lagged country ETF relative-strength rotation with USD/commodity stress gates.

    Returns long-only country ETF weights; UUP/GLD/DBC/SPY are context-only and are
    never assigned weights. Designed for research/backtesting, not live trading advice.
    """
    prices = context.prices.copy()
    if prices.empty:
        return {}
    prices["timestamp"] = pd.to_datetime(prices["timestamp"], utc=True)
    close = prices.pivot(index="timestamp", columns="symbol", values="close").sort_index().ffill()
    selected = [s for s in COUNTRY_SYMBOLS if s in close.columns and s in set(context.symbols)]
    required = selected + [s for s in CONTEXT_SYMBOLS if s in close.columns]
    if len(selected) < 10 or any(s not in close.columns for s in CONTEXT_SYMBOLS) or len(close.dropna(subset=required)) < 130:
        return {s: 0.0 for s in context.symbols}
    close = close.dropna(subset=required)
    returns = close.pct_change().fillna(0.0)
    lag_close = close.iloc[:-1] if close.index[-1] >= pd.Timestamp(context.as_of) else close
    if len(lag_close) < 127:
        return {s: 0.0 for s in context.symbols}
    lag_returns = returns.loc[lag_close.index]
    r63 = lag_close[selected].iloc[-1] / lag_close[selected].iloc[-64] - 1.0
    r126 = lag_close[selected].iloc[-1] / lag_close[selected].iloc[-127] - 1.0
    vol63 = lag_returns[selected].tail(63).std() * math.sqrt(252)
    score = (0.60 * r63 + 0.40 * r126) / vol63.replace(0.0, np.nan)

    u63 = lag_close["UUP"].iloc[-1] / lag_close["UUP"].iloc[-64] - 1.0
    u126 = lag_close["UUP"].iloc[-1] / lag_close["UUP"].iloc[-127] - 1.0
    spy63 = lag_close["SPY"].iloc[-1] / lag_close["SPY"].iloc[-64] - 1.0
    spy126 = lag_close["SPY"].iloc[-1] / lag_close["SPY"].iloc[-127] - 1.0
    dbc63 = lag_close["DBC"].iloc[-1] / lag_close["DBC"].iloc[-64] - 1.0
    gld63 = lag_close["GLD"].iloc[-1] / lag_close["GLD"].iloc[-64] - 1.0

    if u63 > 0.03 or u126 > 0.05:
        score *= 0.82
        for s in ASIA_IMPORTERS & set(score.index):
            score.loc[s] -= 0.05
    if (u63 > 0.06 and spy63 < 0.0) or spy126 < -0.10:
        score *= 0.25
    if dbc63 > gld63 and dbc63 > 0.0:
        for s in EXPORTERS & set(score.index):
            score.loc[s] += 0.10
    elif gld63 > dbc63 and gld63 > 0.04:
        for s in EXPORTERS & set(score.index):
            score.loc[s] -= 0.06

    drawdown_126 = lag_close[selected].iloc[-1] / lag_close[selected].tail(126).max() - 1.0
    score[(drawdown_126 < -0.20) | (vol63 > 0.40)] = -np.inf
    top = score.replace([np.inf, -np.inf], np.nan).dropna().sort_values(ascending=False).head(4)
    signals = {s: 0.0 for s in context.symbols}
    if len(top) == 0 or top.iloc[0] <= 0.0:
        return signals
    inv_vol = 1.0 / vol63[top.index].clip(lower=0.08)
    alloc = inv_vol / inv_vol.sum()
    gross = 1.0
    if u63 > 0.03:
        gross *= 0.75
    if spy63 < 0.0:
        gross *= 0.70
    for s, w in alloc.items():
        signals[s] = float(w * gross)
    return signals
