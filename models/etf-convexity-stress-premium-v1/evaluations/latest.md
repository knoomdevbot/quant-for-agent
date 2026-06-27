# AR-050 evaluation: etf-convexity-stress-premium-v1

- Created UTC: 2026-06-26T10:28:43Z
- Data: Alpaca real OHLCV through qfa/AlpacaGateway; no `--data-csv`; no daemon; no live trades.
- Cost/slippage: qfa native metrics are pre-cost; post-cost proxy subtracts 5.0 bps per one-way target-weight turnover.

## Decision

**Suggested decision: rejected**

Falsified: high redundancy max abs corr 0.8774.

## Key metrics (post-cost proxy)

| Metric | Value |
|---|---:|
| Primary Sharpe | 0.4175 |
| Primary max drawdown | -0.2444 |
| Primary total return | 0.2386 |
| Random median Sharpe | 0.5256 |
| Random p25 Sharpe | -0.1162 |
| Random worst Sharpe | -1.0483 |
| Worst random max drawdown | -0.1537 |
| Positive random-window rate | 75.00% |
| Mean daily one-way turnover | 0.0227 |
| Annualized turnover proxy | 5.71 |
| Estimated annual cost drag | 0.0029 |

## QFA run IDs

- primary: qfa run id `1` (2021-01-04 to 2025-12-15)
- random_1: qfa run id `1` (2020-03-02 to 2020-12-15)
- random_2: qfa run id `1` (2020-09-15 to 2021-08-16)
- random_3: qfa run id `1` (2021-01-15 to 2021-12-15)
- random_4: qfa run id `1` (2021-11-01 to 2022-10-17)
- random_5: qfa run id `1` (2022-01-10 to 2022-12-20)
- random_6: qfa run id `1` (2023-02-01 to 2023-11-30)
- random_7: qfa run id `1` (2024-03-01 to 2024-12-16)
- random_8: qfa run id `1` (2025-01-15 to 2025-12-15)

## Orthogonality

Status: `high_redundancy`; max abs correlation: `0.87741099`. See latest.json for per-artifact details.

## Failure modes

- Turnover and VIXY decay can overwhelm the stress-premium idea in choppy false-alarm regimes.
- Defensive assets can sell off alongside equities in inflation/rate shocks.
- The model is not an options strategy; convexity exposure is approximated through realized-volatility stress and a small VIXY sleeve.

## Suggested children

If rejected, do not refine/directly continue this driver. At most one genuinely divergent child: options-free ETF crash-recovery dispersion allocator using dispersion compression after shocks rather than convexity/VIXY stress exposure.
