# AR-062 evaluation: xsec-etf-defensive-rotation-heldout-corr-v1

- Created: 2026-06-26T11:56:55Z
- Data: Alpaca real market data via qfa AlpacaGateway; no CSV; no `--data-csv`; no daemon; no orders.
- Primary window: 2023-01-01 to 2025-12-31; random windows: 8.
- Cost proxy: external one-way turnover haircut at 10 bps primary and 20 bps stress.

## Primary metrics

| metric | pre-cost qfa | 10 bps | 20 bps |
|---|---:|---:|---:|
| Sharpe | 0.3148 | 0.2678 | 0.2208 |
| Ann. return | 0.0360 | 0.0287 | 0.0213 |
| Ann. vol | 0.1519 | 0.1519 | 0.1519 |
| Max drawdown | -0.2103 | -0.2115 | -0.2127 |
| Win rate | 0.3800 | 0.3800 | 0.3773 |

Primary annualized one-way turnover proxy: 7.1393x.

## Random-window metrics (10 bps)

- Median Sharpe: -0.04525001
- p25 Sharpe: -0.29858548
- Worst Sharpe: -0.61703258
- Positive-window rate: 0.5
- Worst max drawdown including primary: -0.21152364
- Median annualized one-way turnover: 2.89448835x

## Orthogonality

{
  "attempted": true,
  "method": "Pearson correlation of AR-062 10 bps cost-adjusted daily returns versus retained artifact equity-curve returns when available.",
  "comparisons": [
    {
      "alpha": "AR-051",
      "artifact": "models/xsec-etf-defensive-rotation-orthogonal-v1/evaluations/latest.json",
      "correlation": 0.65958938,
      "overlap_periods": 248
    },
    {
      "alpha": "AR-015",
      "artifact": "models/tsmom-voltarget-liquid-etf-randomcost-v1/evaluations/latest.json",
      "correlation": 0.4899176,
      "overlap_periods": 499
    },
    {
      "alpha": "AR-037",
      "status": "unavailable_no_equity_curve",
      "artifact": "models/etf-carry-defensive-allocation-v1/evaluations/latest.json"
    }
  ],
  "max_abs_correlation_available": 0.65958938
}

## Decision

**Suggested decision: rejected.** Rejected: random-window median Sharpe or redundancy target failed after explicit held-out-correlation penalties.

Suggested children: no refinement child if rejected; at most one divergent idea is recorded in `latest.json`.
