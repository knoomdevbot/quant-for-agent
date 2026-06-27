# AR-084 evaluation latest

- Model: `megacap-earnings-volume-vacuum-reversal-v1`
- Data source: Alpaca real market data through qfa/AlpacaGateway, daily bars. No CSV, no `--data-csv`, no daemon, no orders.
- QFA run IDs: primary `1`, random `[1, 1, 1, 1, 1, 1, 1, 1]`. Temporary SQLite DBs deleted.
- Primary 5 bps Sharpe: `0.63444419`; annualized return `0.01587829`; annualized volatility `0.02533439`; max drawdown `-0.01965929`.
- Random-window median Sharpe: `0.07856542`; p25 `-0.77604925`; worst `-1.41967623`; positive rate `0.5`.
- Orthogonality: `pass_available_max_corr_le_0p60`, equal-weight same-universe correlation `-0.09265053`; peer artifacts had no retained daily return streams.
- Suggested decision: **rejected**. Fails falsifier: median or p25 random-window Sharpe non-positive/materially negative after 5 bps costs, or primary 5 bps Sharpe non-positive.

## Warnings
- True public earnings-date calendar was not available through qfa/Alpaca daily OHLCV; model uses abnormal-volume/residual-return event proxy and may include non-earnings events.
- qfa CLI has no native cost/slippage parameter; 5 bps one-way turnover haircut applied in external replay using identical Alpaca bars and model weights.
- Artifacts intentionally prune equity curves, daily returns, weights tails, raw data paths, and temporary DB.
