# AR-046 evaluation: liquidity-exhaustion-recovery-megacap-v1

Completed: 2026-06-26T09:59:10Z

## Data and command discipline

- Data source: Alpaca real market data via qfa/AlpacaGateway daily bars.
- CSV usage: none; `--data-csv` was never used.
- DB handling: temporary SQLite DBs under `/tmp`, removed after run JSON artifacts were retained.
- No daemon, no orders, no trades.

## Primary qfa backtest

- Symbols: AAPL, MSFT, NVDA, AMZN, META, GOOGL, AVGO, TSLA, JPM, LLY
- Range: 2024-01-01 to 2025-12-31, 1Day, 500 periods
- Run artifact: `evaluations/runs/qfa_realdata_2024-01-01_2025-12-31_primary.json`

Pre-cost qfa metrics:

- Sharpe: 0.84859942
- Total return: 0.19136536
- Annualized return: 0.0922616
- Annualized volatility: 0.11068819
- Max drawdown: -0.04429516
- Win rate: 0.012

5 bps turnover-replay metrics:

- Sharpe: 0.80678607
- Total return: 0.17963289
- Max drawdown: -0.04908474
- Total turnover: 20.0
- Active periods: 10

## Random windows

Eight qfa/Alpaca random/stress windows were run without CSV. Median random-window Sharpe after the 5 bps turnover haircut was positive but weak.

- Median pre-cost Sharpe: 0.249733915
- Mean pre-cost Sharpe: 0.1677919
- Positive pre-cost Sharpe windows: 4 / 8
- Median cost-adjusted Sharpe: 0.19746282
- Mean cost-adjusted Sharpe: 0.05088013
- Positive cost-adjusted Sharpe windows: 4 / 8
- Worst cost-adjusted drawdown: -0.07442596

## Orthogonality

Available retained equity curves showed:

- AR-028 correlation: 0.463762 over 499 overlapping daily returns.
- tsmom-voltarget-liquid-etf-randomcost-v1 watchlist correlation: 0.183383.
- Mega-cap equal-weight market proxy correlation: 0.281591.
- SPY proxy correlation: 0.356519.

Several watchlist/accepted artifacts did not retain equity curves, limiting library-wide orthogonality checks.

## Suggested decision

`research_watchlist_not_trade`.

The falsifier was not fully triggered because the median cost-adjusted random-window Sharpe was positive and drawdown was contained. However, the signal is sparse, random-window results are mixed, and parent correlation is moderate. Do not trade without stronger live-cost, broader-regime, and better liquidity-pressure validation.
