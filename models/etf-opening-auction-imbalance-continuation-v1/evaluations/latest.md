# AR-087 Evaluation — ETF opening-auction imbalance continuation

Created: `2026-06-26T15:16:02Z`

## Decision

Suggested decision: **rejected**

Rejected by falsifier: random-window robustness after 10 bps one-way turnover cost did not produce positive p25 Sharpe and turnover/costs dominate the opening-continuation edge.

## Primary real-data intraday evaluation

- Data: Alpaca/qfa real 1Min OHLCV, `2023-10-01` to `2025-12-15`.
- Protocol: first 30 regular-session minutes, enter after opening window, hold 120 minutes, flat overnight.
- 10 bps Sharpe: `-4.27938852`
- Annualized return: `-0.10385271`
- Annualized volatility: `0.02554109`
- Max drawdown: `-0.19477831`
- Win rate: `0.07142857`
- Active days: `160` / `490`
- Mean daily roundtrip turnover: `0.37323106`

## Random/stress windows

- Count: `14`
- Median Sharpe: `-5.84184963`
- p25 Sharpe: `-6.33759196`
- Worst Sharpe: `-7.44248814`
- Positive-window rate: `0.0`
- Worst max drawdown: `-0.04143642`

## Orthogonality

Status: `computed`; max abs corr available: `0.1228216`.

Distinct: AR-087 tests same-day continuation from opening range/VWAP/relative-volume imbalance; AR-079 faded range-expansion close-location reversal breadth near later bars.

## Controls

- no_csv_used: true
- no_data_csv_argument_used: true
- no_daemon: true
- no_orders: true
- raw_daily_paths_retained: false
- db_artifact_retained: false
