# AR-114 Evaluation — municipal-tax-flow-calendar-reversal-v1

- Created: 2026-06-26T23:07:23Z
- Decision: **rejected**
- Data: qfa/Alpaca real daily OHLCV with profile secret values redacted; no CSV, no data-csv argument, no daemon, no orders.
- Artifacts: `evaluations/latest.json`, `evaluations/latest.md`, `evaluations/runs/ar114_qfa_alpaca_real_20260626T230723Z.json`

## Key metrics
- Primary 5 bps Sharpe: -0.78653569 ; ann return: -0.01695934 ; max drawdown: -0.10294565
- 2/10 bps Sharpe: -0.57556704 / -1.12239666
- Random windows: count 30, median Sharpe -1.3008624, p25 -3.40819012, worst -3.98285574, positive rate 0.13333333
- Turnover: avg daily 0.0607944, annualized 15.32018843, activation rate 0.04374159
- Orthogonality: proxy_only_compact, max abs proxy corr 0.91520885

## Decision notes
- Primary 5 bps Sharpe is not positive.
- Random-window p25 Sharpe is below zero.
- Positive-window rate is below 60% gate.
- 10 bps sensitivity Sharpe is not positive.
- Max abs proxy correlation exceeds hard 0.60 threshold.
