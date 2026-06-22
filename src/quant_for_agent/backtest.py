from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .alpha import AlphaContext, load_alpha_function, normalize_weights


@dataclass(frozen=True)
class BacktestConfig:
    model_path: str
    symbols: list[str]
    start: str
    end: str
    timeframe: str = "1Day"
    initial_cash: float = 100_000.0


def run_backtest(config: BacktestConfig, prices: pd.DataFrame) -> dict:
    model_fn = load_alpha_function(config.model_path)
    prices = prices.copy()
    prices["timestamp"] = pd.to_datetime(prices["timestamp"], utc=True)
    start = pd.Timestamp(config.start, tz="UTC")
    end = pd.Timestamp(config.end, tz="UTC")
    prices = prices[
        (prices["symbol"].isin(config.symbols))
        & (prices["timestamp"] >= start)
        & (prices["timestamp"] <= end)
    ].sort_values(["timestamp", "symbol"])
    if prices.empty:
        raise ValueError("No price data for requested symbols/date range")

    close = prices.pivot(index="timestamp", columns="symbol", values="close").ffill().dropna()
    if len(close) < 2:
        raise ValueError("Need at least two price timestamps for backtesting")

    daily_returns = close.pct_change().fillna(0.0)
    equity = float(config.initial_cash)
    curve = []
    portfolio_returns = []
    current_weights = {symbol: 0.0 for symbol in config.symbols}

    for idx, as_of in enumerate(close.index[:-1]):
        historical = prices[prices["timestamp"] <= as_of]
        context = AlphaContext(symbols=config.symbols, prices=historical, as_of=as_of)
        raw_signals = model_fn(context) or {}
        current_weights = normalize_weights(raw_signals, config.symbols)
        next_ret = daily_returns.iloc[idx + 1]
        portfolio_ret = sum(current_weights[symbol] * float(next_ret.get(symbol, 0.0)) for symbol in config.symbols)
        equity *= 1.0 + portfolio_ret
        portfolio_returns.append(portfolio_ret)
        curve.append({"timestamp": close.index[idx + 1].isoformat(), "equity": equity})

    metrics = calculate_metrics(config.initial_cash, equity, portfolio_returns, curve)
    return {
        "model_path": str(Path(config.model_path).expanduser().resolve()),
        "symbols": config.symbols,
        "start": config.start,
        "end": config.end,
        "timeframe": config.timeframe,
        "initial_cash": config.initial_cash,
        "metrics": metrics,
        "equity_curve": curve,
    }


def calculate_metrics(initial_cash: float, final_equity: float, returns: list[float], curve: list[dict]) -> dict:
    arr = np.array(returns, dtype=float)
    total_return = final_equity / initial_cash - 1.0
    periods = max(len(arr), 1)
    annualized_return = (1.0 + total_return) ** (252 / periods) - 1.0 if total_return > -1 else -1.0
    volatility = float(arr.std(ddof=1) * np.sqrt(252)) if len(arr) > 1 else 0.0
    sharpe = float((arr.mean() / arr.std(ddof=1)) * np.sqrt(252)) if len(arr) > 1 and arr.std(ddof=1) else 0.0
    equities = np.array([initial_cash] + [point["equity"] for point in curve], dtype=float)
    running_max = np.maximum.accumulate(equities)
    drawdowns = equities / running_max - 1.0
    win_rate = float((arr > 0).mean()) if len(arr) else 0.0
    return {
        "initial_cash": round(float(initial_cash), 4),
        "final_equity": round(float(final_equity), 4),
        "total_return": round(float(total_return), 8),
        "annualized_return": round(float(annualized_return), 8),
        "annualized_volatility": round(float(volatility), 8),
        "sharpe": round(float(sharpe), 8),
        "max_drawdown": round(float(drawdowns.min()), 8),
        "win_rate": round(win_rate, 8),
        "periods": int(periods),
    }
