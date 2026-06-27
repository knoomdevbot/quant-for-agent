"""AR-122 macro-shock defensive-sector relative stabilization model.

Research-only qfa alpha model. It uses only timestamped daily OHLCV bars supplied
through the qfa AlphaContext and returns target weights; it has no file, daemon,
network, or order side effects.
"""
from __future__ import annotations

import pandas as pd

SELECTED = [
    "SPY",
    "QQQ",
    "IWM",
    "DIA",
    "USMV",
    "SPLV",
    "QUAL",
    "MTUM",
    "XLK",
    "XLY",
    "XLP",
    "XLV",
    "XLU",
    "XLF",
    "XLI",
    "XLE",
    "XLB",
    "XLRE",
    "XLC",
    "HYG",
    "LQD",
    "SHY",
    "IEF",
    "TLT",
    "TIP",
    "GLD",
    "DBC",
]
DEFENSES = ["XLP", "XLV", "XLU", "USMV", "SPLV", "QUAL", "GLD", "IEF", "SHY"]
CYCLICALS = ["XLK", "XLY", "XLF", "XLI", "XLE", "XLB", "IWM", "QQQ", "MTUM"]


def _price_frame(context) -> pd.DataFrame | None:
    prices = getattr(context, "prices", None)
    if prices is None and isinstance(context, dict):
        prices = context.get("prices") or context.get("bars")
    if prices is None or len(prices) == 0:
        return None
    return prices.copy()


def generate_signals(context) -> dict[str, float]:
    """Return event-gated defensive stabilization weights from daily OHLCV history."""
    df = _price_frame(context)
    if df is None or len(df) < 260:
        return {"SHY": 1.0}

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        close = df.pivot(index="timestamp", columns="symbol", values="close").sort_index()
        high = df.pivot(index="timestamp", columns="symbol", values="high").sort_index()
        low = df.pivot(index="timestamp", columns="symbol", values="low").sort_index()
    else:
        close = df["close"]
        high = df["high"]
        low = df["low"]

    if any(symbol not in close.columns for symbol in SELECTED):
        return {"SHY": 1.0}

    close = close[SELECTED].dropna()
    high = high.reindex(close.index)[SELECTED]
    low = low.reindex(close.index)[SELECTED]
    if len(close) < 260:
        return {"SHY": 1.0}

    rets = close.pct_change()
    spy = close["SPY"]
    hyg = close["HYG"]
    tlt = close["TLT"]
    spy1 = spy.pct_change()
    spy3 = spy.pct_change(3)
    hyg3 = hyg.pct_change(3)
    tlt3 = tlt.pct_change(3)
    realized_vol = spy1.rolling(20).std() * (252**0.5)
    vol_rank = realized_vol.rolling(252, min_periods=80).rank(pct=True)
    shock = (
        (spy1 <= -0.018)
        | (spy3 <= -0.04)
        | ((spy3 <= -0.025) & (hyg3 <= -0.012))
        | ((spy3 <= -0.025) & (tlt3 <= -0.018))
        | ((spy1 <= -0.01) & (vol_rank >= 0.80))
    )
    if not bool(shock.tail(8).any()):
        return {"SHY": 1.0}

    cyclical_return = close[CYCLICALS].pct_change(3).mean(axis=1)
    relative_return = close[DEFENSES].pct_change(3).sub(cyclical_return, axis=0)
    close_location = (
        (close[DEFENSES] - low[DEFENSES])
        / (high[DEFENSES] - low[DEFENSES]).replace(0, pd.NA)
    ).rolling(3).mean()
    cyclical_vol = rets[CYCLICALS].rolling(5).std().mean(axis=1)
    defensive_vol = rets[DEFENSES].rolling(5).std()
    vol_compression = defensive_vol.rdiv(cyclical_vol, axis=0)
    score = (
        relative_return.rank(axis=1, pct=True)
        + close_location.rank(axis=1, pct=True)
        + vol_compression.rank(axis=1, pct=True)
    )
    latest_score = score.iloc[-1].dropna().sort_values(ascending=False)
    picks = list(latest_score.head(3).index)
    if not picks:
        return {"SHY": 1.0}

    weights = {pick: 0.95 / len(picks) for pick in picks}
    weights["SHY"] = weights.get("SHY", 0.0) + 0.05
    return weights
