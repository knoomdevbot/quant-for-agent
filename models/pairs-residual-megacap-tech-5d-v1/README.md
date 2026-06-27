# pairs-residual-megacap-tech-5d-v1

AR-005 research model: residual mean reversion among mega-cap tech pairs.

## Hypothesis

Related mega-cap technology/liquid growth equities occasionally diverge due to idiosyncratic flows; residual spreads should mean-revert over several sessions.

## Model

- Universe: AAPL, MSFT, NVDA, AMZN, META, GOOGL
- Pair basket: all pair combinations within the universe
- Formation window: 126 trading sessions
- Residual z-score window: 60 trading sessions
- Entry: absolute residual z-score >= 1.5
- Sizing: aggregate pair legs, demean cross-sectionally, gross-normalize to 1.0, cap single-name absolute weight at 0.25
- QFA interface: `generate_signals(context)` in `model.py`

## Evaluation

Real-data qfa backtest was run with Alpaca market data only; no `--data-csv` was used.

- Period: 2024-01-01 to 2025-12-31
- Timeframe: 1Day
- Initial cash: 100000
- QFA run id: 2
- Run JSON: `evaluations/runs/qfa_realdata_20240101_20251231_run2.json`
- SQLite DB artifact: `evaluations/qfa_realdata.sqlite` (controller may remove before commit)

## Latest metrics, pre-cost

- Final equity: 114929.2225
- Total return: 14.929222%
- Annualized return: 7.264733%
- Annualized volatility: 13.752122%
- Sharpe: 0.57877812
- Max drawdown: -13.227204%
- Win rate: 34.6%
- Periods: 500

## Costs/slippage

Issue requested a 5 bps cost/slippage proxy if supported. The current qfa backtest CLI has no cost/slippage parameter, so costs were documented but not applied. Treat metrics as pre-cost and likely optimistic.

## Suggested decision

Watchlist/refine rather than accept for live trading. The real-data result is positive and interpretable, but the Sharpe is modest and pre-cost; random windows and explicit turnover/cost modeling are needed.
