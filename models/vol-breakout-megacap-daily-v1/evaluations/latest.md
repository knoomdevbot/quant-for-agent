# vol-breakout-megacap-daily-v1

Research-only qfa alpha for AR-004: volatility breakout continuation on mega-cap equities.

## Signal
- Universe: AAPL, MSFT, NVDA, AMZN, META, GOOGL, TSLA.
- Daily true range / ATR breakout: latest range must exceed 1.5x prior 20-day ATR.
- Long when close is in the top 20% of the day's range and above open; short when close is in the bottom 20% and below open.
- Scores use excess range multiple, gross-normalized to 1.0 with 0.25 single-name cap.

## Latest real-data evaluation
- Data source: Alpaca real market data via `qfa backtest` with no `--data-csv`.
- Period: 2024-01-01 to 2025-12-31, 1Day bars.
- Costs/slippage: 5 bps intended assumption documented, but not applied because current qfa backtest CLI has no cost/slippage parameter.
- qfa run id: 1
- SQLite artifact: `evaluations/qfa_realdata.sqlite` created by qfa; controller should remove before commit.

## Metrics (pre-cost)
- Final equity: 71348.5093
- Total return: -0.28651491
- Annualized return: -0.1564594
- Annualized volatility: 0.20937325
- Sharpe: -0.7039863
- Max drawdown: -0.37851101
- Win rate: 0.092
- Periods: 500

## Decision
Reject or research-watchlist only. The model has negative Sharpe and large drawdown before costs, so it fails AR-004 acceptance criteria.

## Child ideas
- Refinement child: AR-004-R1: Volatility breakout continuation with market-regime filter and tighter exit/hold logic to reduce drawdowns and avoid bearish/choppy regimes.
- Divergent child: AR-004-D1: Mega-cap overnight gap-reversal/event-liquidity alpha using open-to-close reversion after large news-driven gaps rather than intraday range continuation.
