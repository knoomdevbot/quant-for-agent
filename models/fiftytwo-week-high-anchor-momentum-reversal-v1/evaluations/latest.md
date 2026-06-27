# AR-128 Evaluation Latest

Run: `ar128_qfa_alpaca_real_20260627T143632Z`; data: real Alpaca/qfa daily OHLCV, 2018-01-01..2026-06-26; primary cost 10 bps one-way.

Guardrails: no CSV, no --data-csv, no daemon, no orders; lagged 252-day extrema; monthly rebalance; equities and ETFs evaluated separately.

## Universe
Equities selected 80/80 after coverage/liquidity filters; ETFs selected 48/48. Static current-symbol pool; survivorship/delisting bias remains a limitation.

## Metrics
| Sleeve/model | Full Sharpe | Ann ret | Max DD | Median RW Sharpe | P25 RW Sharpe | Positive windows | Turnover |
|---|---:|---:|---:|---:|---:|---:|---:|
| equity anchor | 0.39 | 5.30% | -21.52% | 0.28 | -0.06 | 71% | 1.05 |
| equity mom | 0.66 | 14.62% | -22.52% | 0.66 | 0.38 | 83% | 0.48 |
| equity tsmom | 0.79 | 13.94% | -33.38% | 0.94 | 0.49 | 92% | 0.48 |
| equity reversal | 0.25 | 2.05% | -21.12% | 0.56 | -0.05 | 73% | 0.56 |
| equity beta_deflated | 0.69 | 12.33% | -24.72% | 0.55 | 0.28 | 83% | 0.50 |
| equity lowvol | 0.53 | 8.47% | -30.97% | 0.59 | 0.41 | 94% | 0.66 |
| etf anchor | -0.14 | -2.25% | -37.91% | -0.24 | -0.54 | 38% | 0.83 |
| etf mom | -0.04 | -0.62% | -40.19% | 0.12 | -0.34 | 60% | 0.43 |
| etf tsmom | 0.38 | 2.95% | -13.60% | 0.26 | 0.06 | 75% | 0.39 |
| etf reversal | -0.17 | -0.89% | -20.20% | -0.10 | -0.57 | 46% | 0.67 |
| etf beta_deflated | 0.36 | 3.93% | -19.94% | 0.37 | 0.05 | 81% | 0.47 |
| etf lowvol | 0.16 | 0.72% | -14.08% | -0.20 | -0.34 | 42% | 0.43 |
| combined anchor 70/30 | 0.28 | 3.38% | -18.71% | 0.25 | -0.07 | 73% | n/a |

## Orthogonality / ablation notes
- equity_anchor_vs_equity_mom: 0.33
- equity_anchor_vs_equity_reversal: 0.04
- equity_anchor_vs_equity_beta_deflated: 0.44
- equity_anchor_vs_equity_lowvol: 0.22
- equity_anchor_vs_etf_anchor: 0.33
- equity_anchor_vs_etf_mom: 0.20
- equity_anchor_vs_etf_tsmom: 0.31
- etf_anchor_vs_etf_mom: 0.83
- etf_anchor_vs_etf_tsmom: 0.20

Decision: **reject for now**. The equity anchor sleeve is positive but fails incremental value versus simple momentum/TSMOM/low-vol/beta-deflated controls (anchor random p25 Sharpe -0.06 vs equity momentum +0.38 and TSMOM +0.49). The ETF anchor sleeve is negative and fails redundancy/robustness checks (median random-window Sharpe -0.24, p25 -0.54; correlation with ETF momentum 0.83). Consider refinement only if a broader non-survivorship universe shows positive incremental p25 after controls.
