# AR-009 latest evaluation — volume-price-pressure-megacap-v1

Status: completed real-data qfa backtest.

## Data and run

- Data source: Alpaca real market data via qfa backtest.
- CSV fixtures: none; `--data-csv` was omitted.
- Period: 2024-01-01 to 2025-12-31.
- Timeframe: 1Day.
- Universe: AAPL, MSFT, NVDA, AMZN, META, GOOGL, TSLA.
- qfa run ID: 1.
- Raw run JSON: `evaluations/runs/qfa_realdata_20240101_20251231_run1.json`.
- SQLite DB artifact: `evaluations/qfa_realdata.sqlite` was created under the model folder; controller should remove before commit if required.

## Model

Volume-confirmed price pressure continuation:

- 3-day close-to-close return as price pressure.
- 60-day prior-window share-volume z-score and dollar-volume z-score as confirmation.
- Long positive pressure and short negative pressure when abnormal volume confirmation is present.
- Gross-normalized long/short weights with intended 25% single-name cap.

## Metrics, pre-cost

- Final equity: 31334.7748
- Total return: -0.68665225
- Annualized return: -0.44281759
- Annualized volatility: 0.33722715
- Sharpe: -1.55991515
- Max drawdown: -0.72226277
- Win rate: 0.206
- Periods: 500

## Costs/slippage

- Assumption: 5 bps fixed cost/slippage proxy requested by issue.
- Applied: no.
- Status: documented only because current qfa backtest CLI exposes no cost/slippage parameter.

## Interpretation

The seed failed the acceptance threshold on Alpaca real market data: pre-cost Sharpe was strongly negative and max drawdown was severe. Costs would further reduce performance.

Suggested decision: reject for alpha library/trading, or keep only as a negative-result research reference.

## Child ideas

- Refinement child: AR-009-R1: Add market-regime and trend-quality filters plus parameter stability sweep over `return_window=[1,3,5]` and `volume_z_min=[1.0,2.0]` to reduce drawdowns and turnover sensitivity.
- Divergent child: AR-009-D1: Mega-cap intraday reversal after abnormal closing-auction volume imbalance, testing a liquidity-provision driver instead of continuation from daily price pressure.
