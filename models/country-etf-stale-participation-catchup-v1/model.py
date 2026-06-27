from __future__ import annotations

import math
import numpy as np
import pandas as pd

COUNTRY_SYMBOLS = ['EEM', 'FXI', 'EWZ', 'KWEB', 'EWJ', 'MCHI', 'INDA', 'EWY', 'VGK', 'EWT']
CONTEXT_SYMBOLS = ['SPY', 'EFA', 'EEM', 'UUP', 'GLD', 'TLT', 'XLU', 'XLP', 'QQQ']

def generate_signals(context):
    """Country/region ETF stale-participation catch-up/reversal proxy.

    Uses qfa context.prices daily OHLCV. Returns target weights for selected country ETFs only;
    context symbols are residualization/diagnostic inputs and receive zero weight.
    """
    prices = context.prices.copy()
    if prices.empty:
        return {}
    prices["timestamp"] = pd.to_datetime(prices["timestamp"], utc=True)
    close = prices.pivot(index="timestamp", columns="symbol", values="close").sort_index().ffill()
    high = prices.pivot(index="timestamp", columns="symbol", values="high").sort_index().ffill()
    low = prices.pivot(index="timestamp", columns="symbol", values="low").sort_index().ffill()
    volume = prices.pivot(index="timestamp", columns="symbol", values="volume").sort_index().ffill()
    tradable = [s for s in COUNTRY_SYMBOLS if s in close.columns and s in set(context.symbols)]
    required = tradable + [s for s in CONTEXT_SYMBOLS if s in close.columns]
    signals = {s: 0.0 for s in context.symbols}
    if len(tradable) < 10 or any(s not in close.columns for s in CONTEXT_SYMBOLS) or len(close.dropna(subset=required)) < 100:
        return signals
    close = close.dropna(subset=required)
    high = high.reindex(close.index).ffill()
    low = low.reindex(close.index).ffill()
    volume = volume.reindex(close.index).ffill()
    returns = close.pct_change()
    as_of_ts = pd.to_datetime(context.as_of, utc=True)
    lag_close = close.iloc[:-1] if close.index[-1] >= as_of_ts else close
    if len(lag_close) < 91:
        return signals
    i = len(lag_close) - 1
    ret = returns.loc[lag_close.index]
    risk = (0.40 * ret["SPY"] + 0.25 * ret["EFA"] + 0.20 * ret["EEM"] - 0.10 * ret["UUP"] + 0.05 * ret["QQQ"]).fillna(0.0)
    rv = risk.iloc[i-63:i]
    scores = {}
    dollar_vol = lag_close[tradable] * volume.reindex(lag_close.index)[tradable]
    for s in tradable:
        y = ret[s].iloc[i-63:i]
        valid = (~y.isna()) & (~rv.isna())
        beta = 1.0 if valid.sum() < 40 or float(rv[valid].var()) == 0.0 else float(np.cov(y[valid], rv[valid])[0, 1] / np.var(rv[valid]))
        expected = beta * float(risk.iloc[i])
        actual = float(ret[s].iloc[i]) if pd.notna(ret[s].iloc[i]) else 0.0
        vol20 = float(ret[s].iloc[i-20:i].std())
        if not math.isfinite(vol20) or vol20 <= 0.0:
            continue
        tr = float((high[s].reindex(lag_close.index).iloc[i] - low[s].reindex(lag_close.index).iloc[i]) / lag_close[s].iloc[i-1])
        range20 = float(((high[s] / low[s] - 1.0).reindex(lag_close.index).iloc[i-20:i]).median())
        adv = float(dollar_vol[s].iloc[i-20:i].median())
        if not math.isfinite(adv) or adv < 5_000_000:
            continue
        logdv = np.log(dollar_vol[s].iloc[i-20:i+1].replace(0, np.nan)).diff()
        low_part = 0.5 * (1.0 if range20 > 0 and tr / range20 < 0.85 else 0.0) + 0.5 * (1.0 if float(logdv.mean()) < 0.0 else 0.0)
        ret_z = max(-5.0, min(5.0, actual / vol20))
        residual_z = (expected - actual) / vol20
        score = residual_z * (0.5 + low_part) - 0.15 * ret_z * (1.0 - low_part)
        if abs(float(risk.iloc[i])) < 0.0025:
            score *= 0.5
        if math.isfinite(score):
            scores[s] = score
    if len(scores) < 8:
        return signals
    score = pd.Series(scores).sort_values()
    longs = score.tail(3)
    shorts = score.head(3)
    if float(longs.mean()) <= 0.0:
        return signals
    wl = longs.clip(lower=0.0)
    wl = wl / wl.sum() if wl.sum() > 0 else pd.Series(1.0 / len(longs), index=longs.index)
    ws = (-shorts).clip(lower=0.0)
    ws = ws / ws.sum() if ws.sum() > 0 else pd.Series(1.0 / len(shorts), index=shorts.index)
    for s, w in wl.items():
        signals[s] = float(0.9 * 0.55 * w)
    for s, w in ws.items():
        signals[s] = float(-0.9 * 0.45 * w)
    return signals
