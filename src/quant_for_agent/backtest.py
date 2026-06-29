from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from pathlib import Path

import numpy as np
import pandas as pd

from .alpha import AlphaContext, load_alpha_function, normalize_weights

SUPPORTED_BACKTEST_ASSET_CLASSES = {"equity", "crypto"}
SUPPORTED_FILL_MIXES = {"maker", "taker", "mixed", "unknown"}


@dataclass(frozen=True)
class BacktestConfig:
    model_path: str
    symbols: list[str]
    start: str
    end: str
    timeframe: str = "1Day"
    initial_cash: float = 100_000.0
    asset_class: str = "equity"
    fee_maker_bps: float = 0.0
    fee_taker_bps: float = 0.0
    fill_mix: str = "unknown"


def _normalize_asset_class(asset_class: str) -> str:
    normalized = asset_class.strip().lower()
    if normalized not in SUPPORTED_BACKTEST_ASSET_CLASSES:
        supported = ", ".join(sorted(SUPPORTED_BACKTEST_ASSET_CLASSES))
        raise ValueError(f"Unsupported asset_class {asset_class!r}; expected one of: {supported}")
    return normalized


def _normalize_fill_mix(fill_mix: str) -> str:
    normalized = fill_mix.strip().lower()
    if normalized not in SUPPORTED_FILL_MIXES:
        supported = ", ".join(sorted(SUPPORTED_FILL_MIXES))
        raise ValueError(f"Unsupported fill_mix {fill_mix!r}; expected one of: {supported}")
    return normalized


def _fee_model(config: BacktestConfig) -> dict:
    maker_bps = float(config.fee_maker_bps)
    taker_bps = float(config.fee_taker_bps)
    if not isfinite(maker_bps) or not isfinite(taker_bps) or maker_bps < 0 or taker_bps < 0:
        raise ValueError("fee_maker_bps and fee_taker_bps must be finite and non-negative")
    fill_mix = _normalize_fill_mix(config.fill_mix)
    if fill_mix == "maker":
        effective_bps = maker_bps
    elif fill_mix == "taker":
        effective_bps = taker_bps
    elif fill_mix == "mixed":
        effective_bps = (maker_bps + taker_bps) / 2.0
    else:
        effective_bps = 0.0
    return {
        "maker_bps": round(maker_bps, 8),
        "taker_bps": round(taker_bps, 8),
        "fill_mix": fill_mix,
        "effective_bps": round(effective_bps, 8),
    }


def run_backtest(config: BacktestConfig, prices: pd.DataFrame) -> dict:
    asset_class = _normalize_asset_class(config.asset_class)
    fee_model = _fee_model(config)
    fee_rate = fee_model["effective_bps"] / 10_000.0
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
    total_fees = 0.0

    for idx, as_of in enumerate(close.index[:-1]):
        previous_weights = current_weights
        historical = prices[prices["timestamp"] <= as_of]
        context = AlphaContext(symbols=config.symbols, prices=historical, as_of=as_of)
        raw_signals = model_fn(context) or {}
        current_weights = normalize_weights(raw_signals, config.symbols)
        turnover = sum(
            abs(current_weights[symbol] - previous_weights.get(symbol, 0.0))
            for symbol in config.symbols
        )
        fee_amount = equity * turnover * fee_rate
        equity -= fee_amount
        total_fees += fee_amount
        next_ret = daily_returns.iloc[idx + 1]
        portfolio_ret = sum(current_weights[symbol] * float(next_ret.get(symbol, 0.0)) for symbol in config.symbols)
        equity *= 1.0 + portfolio_ret
        portfolio_returns.append(portfolio_ret - (turnover * fee_rate))
        curve.append({"timestamp": close.index[idx + 1].isoformat(), "equity": equity})

    metrics = calculate_metrics(config.initial_cash, equity, portfolio_returns, curve)
    metrics["total_fees"] = round(float(total_fees), 4)
    return {
        "model_path": str(Path(config.model_path).expanduser().resolve()),
        "symbols": config.symbols,
        "asset_class": asset_class,
        "asset_bucket": "crypto" if asset_class == "crypto" else "equity",
        "crypto_label": asset_class == "crypto",
        "fee_model": fee_model,
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
