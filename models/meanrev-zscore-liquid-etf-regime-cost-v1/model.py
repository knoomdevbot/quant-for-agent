"""AR-011 cost-aware regime-filtered liquid ETF mean-reversion alpha.

QFA contract: expose generate_signals(context) returning target weights by symbol.
The model refines AR-002 by only taking 3-day z-score reversal trades when
market/asset trend and volatility regimes are not hostile, and by inverse-vol
scaling active legs before gross normalization. It uses only historical OHLCV
rows with timestamp <= context.as_of supplied by qfa.
"""

from __future__ import annotations

import math

UNIVERSE = ["SPY", "QQQ", "IWM", "TLT", "GLD", "SLV", "XLF", "XLK", "XLE", "XLV"]
RETURN_LOOKBACK_DAYS = 3
Z_WINDOW = 60
ENTRY_Z = 1.5
VOL_WINDOW = 20
TREND_WINDOW = 126
MARKET_TREND_SYMBOL = "SPY"
MAX_ABS_WEIGHT = 0.20
# Do not run mean reversion during high-stress market volatility regimes.
MARKET_VOL_CUTOFF = 0.28
ASSET_VOL_CUTOFF = 0.45
MIN_HISTORY = max(Z_WINDOW + RETURN_LOOKBACK_DAYS + 1, TREND_WINDOW + 1, VOL_WINDOW + 1)


def _zero_weights(symbols):
    return {symbol: 0.0 for symbol in symbols}


def _annualized_vol(returns):
    if len(returns) < 2:
        return float("nan")
    return float(returns.std(ddof=1) * math.sqrt(252.0))


def _gross_normalize_capped(raw_scores, symbols):
    gross_score = sum(abs(v) for v in raw_scores.values())
    if gross_score <= 0.0:
        return _zero_weights(symbols)

    weights = {symbol: raw_scores.get(symbol, 0.0) / gross_score for symbol in symbols}
    capped = {symbol: max(-MAX_ABS_WEIGHT, min(MAX_ABS_WEIGHT, float(weights.get(symbol, 0.0)))) for symbol in symbols}
    capped_gross = sum(abs(v) for v in capped.values())
    if capped_gross <= 0.0:
        return _zero_weights(symbols)
    return {symbol: float(capped[symbol] / capped_gross) for symbol in symbols}


def generate_signals(context):
    """Return regime-filtered one-day reversal target weights.

    Signal mechanics:
    - compute each ETF's latest trailing 3-day return z-score over 60 samples;
    - only trade if SPY is above its 126-day average and SPY 20-day realized vol
      is below 28% annualized;
    - buy negative z-score stretches only when the ETF remains above its own
      126-day trend; short positive stretches only when the ETF is below its own
      126-day trend, avoiding shorts into persistent uptrends;
    - scale scores by inverse 20-day realized vol and cap concentration.
    """

    symbols = list(getattr(context, "symbols", []) or [])
    if not symbols:
        return {}

    prices = getattr(context, "prices", None)
    if prices is None or prices.empty:
        return _zero_weights(symbols)
    if not {"timestamp", "symbol", "close"}.issubset(set(prices.columns)):
        return _zero_weights(symbols)

    close = (
        prices[prices["symbol"].isin(symbols)]
        .pivot(index="timestamp", columns="symbol", values="close")
        .sort_index()
        .ffill()
    )
    if close.empty or len(close) < MIN_HISTORY:
        return _zero_weights(symbols)

    # Market-wide adverse regime filter using SPY when available.
    if MARKET_TREND_SYMBOL in close.columns:
        market = close[MARKET_TREND_SYMBOL].dropna()
        if len(market) < MIN_HISTORY:
            return _zero_weights(symbols)
        market_ret = market.pct_change().dropna()
        market_vol = _annualized_vol(market_ret.iloc[-VOL_WINDOW:])
        market_sma = float(market.iloc[-TREND_WINDOW:].mean())
        market_last = float(market.iloc[-1])
        if (not math.isfinite(market_vol)) or market_vol > MARKET_VOL_CUTOFF or market_last < market_sma:
            return _zero_weights(symbols)

    raw_scores = {}
    for symbol in symbols:
        if symbol not in close.columns:
            raw_scores[symbol] = 0.0
            continue
        series = close[symbol].dropna()
        if len(series) < MIN_HISTORY:
            raw_scores[symbol] = 0.0
            continue

        returns_1d = series.pct_change().dropna()
        asset_vol = _annualized_vol(returns_1d.iloc[-VOL_WINDOW:])
        if (not math.isfinite(asset_vol)) or asset_vol <= 0.0 or asset_vol > ASSET_VOL_CUTOFF:
            raw_scores[symbol] = 0.0
            continue

        three_day_returns = series.pct_change(RETURN_LOOKBACK_DAYS).dropna()
        trailing = three_day_returns.iloc[-Z_WINDOW:]
        if len(trailing) < Z_WINDOW:
            raw_scores[symbol] = 0.0
            continue
        mean = float(trailing.mean())
        std = float(trailing.std(ddof=1))
        last = float(trailing.iloc[-1])
        if (not math.isfinite(std)) or std <= 0.0:
            raw_scores[symbol] = 0.0
            continue

        z_score = (last - mean) / std
        if abs(z_score) < ENTRY_Z:
            raw_scores[symbol] = 0.0
            continue

        trend_sma = float(series.iloc[-TREND_WINDOW:].mean())
        in_uptrend = float(series.iloc[-1]) >= trend_sma
        # Long oversold ETFs only when the intermediate trend is still positive;
        # short overbought ETFs only when the ETF is not in a persistent uptrend.
        if z_score <= -ENTRY_Z and in_uptrend:
            raw_scores[symbol] = abs(z_score) / asset_vol
        elif z_score >= ENTRY_Z and not in_uptrend:
            raw_scores[symbol] = -abs(z_score) / asset_vol
        else:
            raw_scores[symbol] = 0.0

    return _gross_normalize_capped(raw_scores, symbols)
