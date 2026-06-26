# AR-095 Evaluation — sector ETF volume exhaustion reversal

Suggested decision: **rejected**.

Real Alpaca/qfa OHLCV only; no CSV, no daemon, no orders. External cost proxy: 5 bps one-way turnover.

## Key metrics (cost-adjusted random windows)
- Mean Sharpe: -0.25417176
- Median Sharpe: -0.29281638
- p25 Sharpe: -0.79435349
- Worst Sharpe: -2.05827009
- Positive-window rate: 0.4
- Mean annualized return: -0.00443112
- Mean annualized volatility: 0.0267691
- Worst max drawdown: -0.05862576

Primary 2024-2025 cost-adjusted Sharpe: 0.158675; annualized return 0.0031579; max drawdown -0.02815039.

Orthogonality: unavailable; relevant retained artifacts did not provide compact daily return streams.
