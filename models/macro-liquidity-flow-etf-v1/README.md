# macro-liquidity-flow-etf-v1 (AR-042)

Research-only qfa alpha for scheduled macro/liquidity ETF flow pressure. The model uses only qfa/Alpaca daily OHLCV bars plus deterministic calendar proxies; no external CSV fixtures, no daemon, and no live trading.

## Hypothesis

ETF flow pressure around recurring macro/liquidity-risk periods may be more informative than plain calendar month boundaries when combined with cross-asset breadth shifts across equities, duration, gold, utilities, and energy.

## Signal

Universe: `SPY`, `QQQ`, `IWM`, `TLT`, `GLD`, with `XLU`/`XLE` included as liquid defensive/energy pressure sleeves.

Scheduled proxies are deterministic from date only:

- First-Friday payroll proxy, +/- one business day.
- CPI proxy: weekdays around days 10-14.
- FOMC proxy: third Wednesday in regular meeting months, +/- one business day.
- Mid-quarter liquidity proxy in February/May/August/November.

On event-proxy days the model runs up to 1.0 gross; on non-event days it retains a smaller 0.35 gross cross-asset pressure allocation. Weights are long-only, capped at 35%, and use only lagged OHLCV-derived returns, volatility, breadth, and dollar-volume pressure.

## Evaluation

- Data: qfa `AlpacaGateway` real daily OHLCV, 2019-01-01 through 2025-12-31 fetch, 12,313 rows.
- Main backtest: 2021-01-01 through 2025-12-31.
- Costs/slippage: qfa native costs are not supported by the repo backtester, so an ex-post 5 bps one-way turnover haircut was applied: `net_return = gross next-day close-to-close return - sum(abs(delta_weight))*0.0005`.
- Random-period protocol: 10 seeded windows, each 252/378/504 business days, using the same real Alpaca OHLCV data.

## Results after costs

| Metric | Value |
|---|---:|
| Main Sharpe | 0.28685493 |
| Main annualized return | 0.02975948 |
| Main annualized volatility | 0.13452332 |
| Main max drawdown | -0.19272499 |
| Main avg daily turnover | 0.14361997 |
| Median random-window Sharpe | 0.73544359 |
| p25 random-window Sharpe | 0.03605889 |
| Worst random-window Sharpe | -0.68603458 |
| Positive random-window rate | 0.70 |
| Worst random-window max drawdown | -0.18545267 |

Random-window Sharpes: `1.00586758, 1.00169521, 0.84417666, 4.68999737, -0.00715490, 0.62671052, -0.28350081, 1.02670799, -0.68603458, 0.16570027`.

## Orthogonality / redundancy

Feasible same-date return-stream check on the same AR-042 symbol/data set found high correlation to `turn-month-calendar-window-etf-v1`: `0.969061`. Some other comparisons were not meaningful because those models did not accept this universe in the quick compatibility run.

## Decision

**Suggested decision: reject/park; do not refine this implementation.**

The random-window median Sharpe is positive after costs, but the high correlation to an AR-021-style turn-month calendar model triggers the redundancy falsifier. Main-period Sharpe is also weak at 0.28685493, with a -19.27% max drawdown.

## Divergent child idea

Intraday post-macro ETF liquidity-vacuum reversal: after large same-day range expansion in SPY/TLT/GLD on scheduled-proxy days, fade the lagging asset next session with volatility-scaled gross and no month-boundary terms.
