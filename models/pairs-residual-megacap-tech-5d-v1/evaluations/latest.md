# AR-005 latest evaluation

Model: `pairs-residual-megacap-tech-5d-v1`

## Run

- Command used real Alpaca market data through qfa; no `--data-csv`.
- Period: 2024-01-01 to 2025-12-31
- Symbols: AAPL, MSFT, NVDA, AMZN, META, GOOGL
- Timeframe: 1Day
- Initial cash: 100000
- QFA DB artifact: `evaluations/qfa_realdata.sqlite`
- QFA run id: 2
- Run JSON: `evaluations/runs/qfa_realdata_20240101_20251231_run2.json`

## Metrics, pre-cost

- Final equity: 114929.2225
- Total return: 0.14929222
- Annualized return: 0.07264733
- Annualized volatility: 0.13752122
- Sharpe: 0.57877812
- Max drawdown: -0.13227204
- Win rate: 0.346
- Periods: 500

## Costs/slippage

- Requested assumption: 5 bps
- Applied in qfa run: no
- Reason: current qfa backtest CLI exposes no costs/slippage argument.

## Interpretation

Positive 2024-2025 real-data result, but modest Sharpe and pre-cost. The strategy enters after the 126/60-day warmup and has periods of no exposure. Treat as promising but not accepted without cost-aware robustness checks.

## Suggested decision

Watchlist/refine; not accepted for live trading.

## Child ideas

- Refinement child: AR-005-R1 adaptive pair selection with rolling correlation/ADF filters and turnover/cost gate.
- Divergent child: AR-005-D1 mega-cap tech intraday overnight-gap reversal using open-to-close residuals.
