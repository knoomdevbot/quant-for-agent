# AR-067 Evaluation — etf-defensive-carry-surprise-allocator-v1

- Data: Alpaca real daily OHLCV through qfa CLI/AlpacaGateway; no CSV, no `--data-csv`.
- Safety: no daemon, no orders, temporary SQLite DB removed.
- Costs/slippage: qfa native costs unavailable; applied ex-post 5 bps one-way turnover haircut.
- Raw daily paths retained: false.

## Results (5 bps cost-adjusted)

| Metric | Value |
|---|---:|
| Primary annualized return | -0.02179576 |
| Primary annualized volatility | 0.12343065 |
| Primary max drawdown | -0.23706118 |
| Primary Sharpe | -0.11339291 |
| Annualized turnover proxy | 16.4333637 |
| Median random-window Sharpe | 0.38330564 |
| p25 random-window Sharpe | -0.0879759 |
| Worst random-window Sharpe | -1.0376568 |
| Positive window rate | 0.66666667 |
| Max available abs correlation | 0.94162767 |

Suggested decision: **rejected**.

Rationale: Rejected: random-window p25 Sharpe after 5 bps costs was not positive and/or max available retained-curve correlation breached 0.60.

## QFA run IDs

- Smoke: 1
- Primary: 2
- Random: {'random_1': 3, 'random_2': 4, 'random_3': 5, 'random_4': 6, 'random_5': 7, 'random_6': 8}

## Artifact flags

`raw_daily_paths_retained:false`, `no_csv_used:true`, `no_data_csv_argument_used:true`, `no_daemon:true`, `no_orders:true`.
