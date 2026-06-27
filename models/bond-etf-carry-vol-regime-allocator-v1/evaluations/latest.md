# AR-086 Evaluation — bond ETF carry/vol regime allocator

Created: `2026-06-26T15:08:19Z`

## Decision

Suggested decision: **rejected**

Rejected: random-window robustness after 5 bps costs did not clear positive median and p25 Sharpe requirements; bad-result pruning means no direct refinement child is proposed.

## Primary qfa/Alpaca backtest with 5 bps one-way turnover-cost proxy

- Sharpe: `0.00836755`
- Annualized return: `-0.00131945`
- Annualized volatility: `0.06046549`
- Max drawdown: `-0.19376816`
- Win rate: `0.44852354`
- Mean daily turnover: `0.06455467`

## Random/stress windows

- Count: `12`
- Median Sharpe: `-0.24134084`
- p25 Sharpe: `-0.84694713`
- Worst Sharpe: `-1.38871688`
- Positive-window rate: `0.33333333`
- Worst max drawdown: `-0.10752993`

## Orthogonality

Status: `computed`; max abs corr available: `0.76055498`.

## Controls

- no_csv_used: true
- no_data_csv_argument_used: true
- no_daemon: true
- no_orders: true
- raw_daily_paths_retained: false
