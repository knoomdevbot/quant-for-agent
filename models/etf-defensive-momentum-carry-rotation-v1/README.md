# ETF defensive momentum carry rotation v1 (AR-059)

QFA-compatible long-only ETF rotation model over SPY, QQQ, IWM, TLT, GLD, HYG, LQD, and XLU.

The model uses only historical OHLCV bars available inside `generate_signals(context)`. It combines 63/126-day momentum, realized volatility, recent drawdown, and trend-stability/carry proxies. A SPY/QQQ/HYG-vs-LQD stress gate shifts budget from equity/credit ETFs toward defensive ETFs during stressed regimes. Per-ETF weights are capped at 35%, max gross is 1.0, and residual cash is allowed.

Evaluation artifacts are under `evaluations/` and were generated using Alpaca real market data through qfa/AlpacaGateway only. No CSV data, no `--data-csv`, no daemon, and no orders/trades.
