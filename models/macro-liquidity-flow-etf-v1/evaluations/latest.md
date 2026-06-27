# AR-042 evaluation: macro-liquidity-flow-etf-v1

Created: 2026-06-26T09:41:05Z

## Data and protocol

- Source: qfa `AlpacaGateway` real Alpaca daily OHLCV only; no CSV and no `--data-csv`.
- Symbols: SPY, QQQ, IWM, TLT, GLD, XLU, XLE.
- Fetch range: 2019-01-01 to 2025-12-31; rows: 12,313.
- Main evaluation: 2021-01-01 to 2025-12-31.
- Random-period protocol: 10 seeded windows of 252/378/504 business days.
- Costs: 5 bps one-way ex-post turnover haircut because qfa native costs are not supported by the repo backtester.

## Key metrics after costs

| Metric | Value |
|---|---:|
| Main Sharpe | 0.28685493 |
| Main annualized return | 0.02975948 |
| Main annualized volatility | 0.13452332 |
| Main max drawdown | -0.19272499 |
| Main avg daily turnover | 0.14361997 |
| Median random Sharpe | 0.73544359 |
| p25 random Sharpe | 0.03605889 |
| Worst random Sharpe | -0.68603458 |
| Positive window rate | 0.70 |
| Worst random max drawdown | -0.18545267 |

Random-window Sharpes: 1.00586758, 1.00169521, 0.84417666, 4.68999737, -0.00715490, 0.62671052, -0.28350081, 1.02670799, -0.68603458, 0.16570027.

## Orthogonality

- `turn-month-calendar-window-etf-v1`: same-date return correlation 0.969061 on the same AR-042 symbols/data compatibility run.
- Other quick checks were not meaningful where models did not accept the AR-042 universe.

## Decision

**Reject/park; do not refine this implementation.**

Although the median random-window Sharpe is positive after costs, the AR-042 falsifier includes high redundancy. The observed 0.969061 correlation to an AR-021-style turn-month calendar model is too high for a divergent child alpha. Main Sharpe is also weak and max drawdown is material.

## Divergent child idea

Intraday post-macro ETF liquidity-vacuum reversal: after large same-day range expansion in SPY/TLT/GLD on scheduled-proxy days, fade the lagging asset next session with volatility-scaled gross and no month-boundary terms.
