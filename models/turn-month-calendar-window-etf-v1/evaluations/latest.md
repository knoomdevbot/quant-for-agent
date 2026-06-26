# AR-021 Evaluation: turn-month-calendar-window-etf-v1

## Scope
- Data source: Alpaca real market data through qfa AlpacaGateway only.
- CSV usage: none; `--data-csv` was not used.
- Trading: no trades placed; qfa daemon not run.
- Runtime DB: `/tmp/qfa_ar021.sqlite3`; not retained.

## Primary qfa backtest
- Symbols: SPY, QQQ, IWM, TLT, GLD
- Window: 2021-01-01 to 2025-12-31
- Timeframe: 1Day
- qfa run id: 1

Pre-cost qfa metrics:
- Total return: 0.47031678
- Annualized return: 0.08061063
- Annualized volatility: 0.13355703
- Sharpe: 0.64718778
- Max drawdown: -0.26322576
- Win rate: 0.53232243
- Periods: 1253

Cost-haircut metrics:
- Total return: 0.3833081
- Annualized return: 0.0674345
- Annualized volatility: 0.13358099
- Sharpe: 0.55523109
- Max drawdown: -0.27131907
- Win rate: 0.528332
- Periods: 1253

## Random windows
- Protocol: 8 seeded random windows, qfa/Alpaca real data only.
- qfa run ids: 2, 3, 4, 5, 6, 7, 8, 9
- Seed: 21021

Cost-haircut Sharpe summary:
- Min: -1.43748385
- Median: 0.5829092
- Mean: 0.29564799
- Max: 1.38249264

Cost-haircut total-return summary:
- Min: -0.18393039
- Median: 0.05463321
- Mean: 0.02601957
- Max: 0.17756052

## Costs/slippage
qfa's current backtester has no native transaction-cost/slippage parameter. The retained artifact applies an ex-post 5 bps haircut per estimated gross-turnover event when the model changes between flat and active states. Primary estimated gross-turnover events: 122; estimated total cost fraction: 0.061.

## Orthogonality
Computed daily equity-curve return correlation against AR-006 parent `turn-month-liquid-etf-seasonality-v1` over 499 overlapping periods: 0.50325754. This is only moderately orthogonal and should be treated as a refinement of AR-006.

## Decision
Suggested decision: watchlist / continue research, non-rejected. Median random-window Sharpe is positive after costs, but the strategy remains regime-fragile with negative random windows and large drawdowns; not production-ready.

## Child issues
- AR-041: volatility/regime-gated turn-of-month ETF seasonality.
- AR-042: scheduled macro/liquidity ETF flow pressure using cross-asset breadth.
