# AR-071 evaluation: etf-realized-skew-crash-rebound-breadth-v1

- Created: 2026-06-26T12:55:22Z
- Data: Alpaca real market data via qfa AlpacaGateway; no CSV; no `--data-csv`; no daemon; no orders.
- Primary window: 2020-01-01 to 2025-12-31; symbols available: SPY, QQQ, IWM, XLV, XLY, XLE, XLU, XLP, TLT, IEF, GLD, HYG, LQD, SHY.
- Random windows: 10 deterministic pseudo-random windows.
- Cost proxy: external one-way turnover haircut at 5 bps and 10 bps.
- Temporary qfa DB: /tmp/qfa-ar-071.sqlite3; removed after run; durable raw daily paths/equity curves/weights retained: false.

## Primary metrics

| metric | pre-cost qfa | 5 bps | 10 bps |
|---|---:|---:|---:|
| Sharpe | 0.1009 | -0.1634 | -0.4255 |
| Ann. return | 0.0051 | -0.0198 | -0.0441 |
| Ann. vol | 0.0947 | 0.0949 | 0.0953 |
| Max drawdown | -0.1607 | -0.2300 | -0.3135 |
| Win rate | 0.4874 | 0.4668 | 0.4608 |

Primary annualized one-way turnover proxy at 10 bps basis: 50.1155x.

## Random-window metrics (10 bps)

- Median Sharpe: -0.36645007
- p25 Sharpe: -0.91447936
- Worst Sharpe: -2.00177956
- Positive-window rate: 0.3
- Median annualized one-way turnover: 34.48796103x
- Worst max drawdown including primary: -0.31354638

## Orthogonality

Status: **pass_low_available_correlation**

```json
{
  "attempted": true,
  "status": "pass_low_available_correlation",
  "method": "Pearson correlation of AR-071 10 bps cost-adjusted primary daily returns against retained artifact equity curves when available.",
  "comparisons": [
    {
      "alpha": "AR-051",
      "status": "unavailable_no_retained_equity_curve",
      "artifact": "models/xsec-etf-defensive-rotation-orthogonal-v1/evaluations/latest.json"
    },
    {
      "alpha": "AR-062",
      "artifact": "models/xsec-etf-defensive-rotation-heldout-corr-v1/evaluations/latest.json",
      "correlation": 0.16020271,
      "overlap_periods": 749
    },
    {
      "alpha": "AR-043",
      "status": "unavailable_no_retained_equity_curve",
      "artifact": "models/etf-carry-defensive-orthogonal-v1/evaluations/latest.json"
    }
  ],
  "max_abs_correlation_available": 0.16020271
}
```

## Decision

**Suggested decision: rejected.** Rejected by falsifier: cost-adjusted random-window median Sharpe is not positive enough after turnover costs, p25 is weak/materially negative, turnover is high, or orthogonality could not be proven.

Suggested children are recorded in `latest.json`; no refinement child is proposed if rejected.
