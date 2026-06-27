# AR-074 Evaluation — macro-event liquidity-gap ETF recovery allocator

Created: `2026-06-26T13:24:40Z`

## Decision

Suggested decision: **rejected**

Rejected by falsifier: random/stress robustness after 10 bps one-way turnover costs failed the positive p25 Sharpe requirement.

## Primary qfa/Alpaca backtest with 10 bps one-way turnover-cost proxy

- Sharpe: `-0.35085969`
- Annualized return: `-0.05621763`
- Annualized volatility: `0.13761961`
- Max drawdown: `-0.39773669`
- Win rate: `0.46679947`
- Mean daily turnover: `0.32017684`

## Random/stress windows

- Count: `12`
- Median Sharpe: `-0.68668877`
- p25 Sharpe: `-1.36313819`
- Worst Sharpe: `-1.97529341`
- Positive-window rate: `0.25`
- Worst max drawdown: `-0.23611909`

## Orthogonality

Status: `computed`; max abs corr available: `0.76716417`.

## Controls

- no_csv_used: true
- no_data_csv_argument_used: true
- no_daemon: true
- no_orders: true
- raw_daily_paths_retained: false
