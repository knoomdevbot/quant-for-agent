# AR-053 latest evaluation

- Created: 2026-06-26T10:43:58Z
- Data: Alpaca real OHLCV via qfa; no CSV / no `--data-csv`
- Symbols: SPY, QQQ, IWM, TLT, GLD, XLU, XLE
- Primary window: 2021-01-04 to 2025-12-15
- Costs: 5 bps one-way ex-post turnover haircut
- QFA run IDs: 1, 1, 1, 1, 1, 1, 1, 1, 1, 1

## Key metrics after costs

| Metric | Value |
|---|---:|
| Primary Sharpe | 0.49240692 |
| Primary annualized return | 0.0324517 |
| Primary annualized vol | 0.06975364 |
| Primary max drawdown | -0.13532074 |
| Median random-window Sharpe | 0.18538839 |
| p25 random-window Sharpe | -0.5284254 |
| Worst random-window Sharpe | -1.01566838 |
| Positive random-window rate | 0.5 |
| Mean daily turnover | 0.1002045 |

## Orthogonality

low_to_moderate_redundancy; max abs correlation 0.29718076.

## Suggested decision

**reject_or_park_do_not_refine** — Fails acceptance: primary post-cost Sharpe 0.49240692, median random Sharpe 0.18538839, p25 random Sharpe -0.52842540, orthogonality status low_to_moderate_redundancy.

## Warnings

- Deterministic macro proxies are not official event timestamps.
- Daily qfa backtester is close-to-close, not true intraday.
- Temporary SQLite DBs were deleted; db_artifact_retained=false.
