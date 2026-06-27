# AR-104 evaluation: broad-etf-tsmom-correlation-cluster-riskbudget-v1

- Created: 2026-06-26T17:28:10Z
- Data: Alpaca real market data through qfa; no CSV; no `--data-csv`; no daemon; no orders.
- Required booleans: no_csv_used=true; no_data_csv_argument_used=true; no_daemon=true; no_orders=true; raw_daily_paths_retained=false.
- Primary window: 2022-01-03 to 2025-12-31; random windows: 6.
- Cost proxy: external one-way turnover haircut at 5/10/20 bps.
- Limitation: bounded recovery used compact protocol (primary + six random windows) and does not retain raw daily bars/equity/weights paths.

## Primary metrics

- Pre-cost qfa: Sharpe 0.3151; ann return 0.0266; ann vol 0.0993; max DD -0.1004.
- 5 bps: Sharpe 0.1326; ann return 0.0082; max DD -0.1152.
- 10 bps: Sharpe -0.0500; ann return -0.0099; max DD -0.1464.
- 20 bps: Sharpe -0.4147; ann return -0.0452; max DD -0.2291.
- Primary annualized one-way turnover proxy: 36.2495x.
- Primary mean max macro-cluster gross: 0.48524699; p95 max macro-cluster gross: 0.7213122.

## Random-window metrics at 10 bps

- Median Sharpe: -0.17854859
- p25 Sharpe: -0.5751906
- Worst Sharpe: -2.48863265
- Positive-window rate: 0.5
- Worst max drawdown including primary: -0.14644236
- Median annualized one-way turnover: 36.61366227x

## Orthogonality

```json
{
  "attempted": true,
  "method": "Pearson correlation of AR-104 10 bps daily returns versus retained artifact equity-curve returns where available.",
  "comparisons": [
    {
      "alpha": "AR-015",
      "correlation": 0.65292187,
      "overlap_periods": 499,
      "artifact": "models/tsmom-voltarget-liquid-etf-randomcost-v1/evaluations/latest.json"
    },
    {
      "alpha": "AR-036",
      "status": "unavailable_no_retained_equity_curve",
      "artifact": "models/etf-carry-defensive-turnover-brake-v1/evaluations/latest.json"
    },
    {
      "alpha": "AR-062",
      "correlation": 0.74805495,
      "overlap_periods": 749,
      "artifact": "models/xsec-etf-defensive-rotation-heldout-corr-v1/evaluations/latest.json"
    }
  ],
  "max_abs_correlation_available": 0.74805495
}
```

## Decision

**Suggested decision: rejected.** Rejected: compact real-data random-window protocol did not meet the robustness and orthogonality gate.

No direct refinement/extension child is proposed if rejected.
