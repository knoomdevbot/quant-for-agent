# AR-083 Evaluation — Sector ETF breadth-confirmed defensive trend allocator

Created: `2026-06-26T14:36:08Z`

## Suggested decision

**rejected** — p25 random-window Sharpe negative after 5 bps costs; max drawdown at or beyond unacceptable ~20% threshold

## Primary results

Window `2024-01-02` to `2025-12-15`; after-cost Sharpe `-0.39731969`, annualized return `-0.09743285`, annualized volatility `0.20057746`, max drawdown `-0.25603581`, win rate `0.37218814`.

## Random / stress windows

Count `10`; median Sharpe `0.1370738`; p25 Sharpe `-0.04859923`; worst Sharpe `-0.82848241`; positive-window rate `0.7`; worst max drawdown `-0.25603581`.

## Orthogonality

Status `unavailable`; max abs corr `None`.


## Controls

- no_csv_used: true
- no_data_csv_argument_used: true
- no_daemon: true
- no_orders: true
- db_artifact_retained: false
- raw_daily_paths_retained: false

Command provenance: credentials were sourced from the configured secret profile with values redacted; qfa/Alpaca daily bars were used without CSV input, daemon, or order commands.

## Child suggestion policy

Rejected: no refinement/direct extension suggested. Divergent child only: **Sector ETF post-rebalance volume exhaustion reversal allocator** — Different return driver: reversal after abnormal sector ETF volume/range exhaustion, not breadth-confirmed trend or defensive leadership.
