# AR-147 latest evaluation

Decision: **rejected**.

Rejected: failed strict fast-falsification gates: max_relevant_correlation_above_0_60

| Metric | Value |
|---|---:|
| Primary 10 bps Sharpe | 0.48697177 |
| Primary ann. return | 0.0482893 |
| Primary max drawdown | -0.20511827 |
| Random median Sharpe | 0.78305925 |
| Random p25 Sharpe | 0.39129277 |
| Positive random windows | 0.875 |
| 20 bps Sharpe | 0.33790794 |
| Shifted-label Sharpe | 0.24736634 |
| Inverted-label Sharpe | 0.25367064 |
| TSMOM baseline Sharpe | 0.48992916 |
| Max relevant correlation | 0.62351781 |

Provenance booleans: `no_csv_used=true`, `no_data_csv_argument_used=true`, `no_daemon=true`, `no_orders=true`, `raw_daily_paths_retained=false`.

Source/timestamp gate: H.4.1 scheduled Thursday 16:30 ET release and next-session entry are feasible; current FRED history was used for this compact scout, so revision/vintage audit remains a caveat.
