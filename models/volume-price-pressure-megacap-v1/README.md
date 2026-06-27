# volume-price-pressure-megacap-v1

Research artifact for **AR-009 — Volume-confirmed price pressure continuation**.

## Hypothesis

Short-horizon price moves in liquid mega-cap equities that occur with abnormal share volume or dollar volume may reflect informed/forced flows and continue over the next daily bar.

## Universe

- AAPL
- MSFT
- NVDA
- AMZN
- META
- GOOGL
- TSLA

## Signal

- Timeframe: daily OHLCV from Alpaca real market data.
- Price pressure: 3-session close-to-close return.
- Volume confirmation: latest share-volume and dollar-volume z-scores versus the prior 60 sessions.
- Entry direction: long positive pressure, short negative pressure, only when share-volume or dollar-volume confirmation is above threshold.
- Sizing: signed return times confirmation strength, gross-normalized, with a 25% intended single-name cap where feasible.

## Evaluation

Ran qfa backtest over 2024-01-01 through 2025-12-31 using Alpaca market data. No `--data-csv` or CSV fixture was used.

Pre-cost metrics:

- Final equity: 31334.7748
- Total return: -0.68665225
- Annualized return: -0.44281759
- Annualized volatility: 0.33722715
- Sharpe: -1.55991515
- Max drawdown: -0.72226277
- Win rate: 0.206
- Periods: 500

Costs/slippage: intended 5 bps assumption documented, but not applied because current qfa backtest CLI has no cost/slippage parameter.

Decision recommendation: reject for alpha library/trading; negative pre-cost Sharpe and severe drawdown fail the issue acceptance threshold.

## Artifacts

- `model.py`: QFA-compatible `generate_signals(context)` implementation.
- `config.yaml`: model configuration and latest evaluation summary.
- `metadata.yaml`: research metadata and child ideas.
- `evaluations/latest.json`: structured evaluation summary.
- `evaluations/latest.md`: human-readable evaluation summary.
- `evaluations/runs/qfa_realdata_20240101_20251231_run1.json`: raw qfa run output.
- `evaluations/qfa_realdata.sqlite`: qfa SQLite DB artifact created during evaluation; controller should remove before commit if required.

## Child ideas

- Refinement: AR-009-R1: Add market-regime and trend-quality filters plus parameter stability sweep over `return_window=[1,3,5]` and `volume_z_min=[1.0,2.0]` to reduce drawdowns and turnover sensitivity.
- Divergent: AR-009-D1: Mega-cap intraday reversal after abnormal closing-auction volume imbalance, testing a liquidity-provision driver instead of continuation from daily price pressure.
