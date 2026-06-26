# AR-073 evaluation: etf-relief-rally-exhaustion-reversal-v1

- Created: 2026-06-26T13:24:13Z
- Data: Alpaca real market data via qfa AlpacaGateway; no CSV; no `--data-csv`; no daemon; no orders.
- Primary window: 2020-01-01 to 2025-12-31; symbols available: SPY, QQQ, IWM, XLE, XLY, XLV, XLP, XLU, TLT, IEF, GLD, HYG, LQD, SHY.
- Random/stress windows: 12.
- Cost proxy: external one-way turnover haircut at 5 bps and 10 bps.
- Temporary qfa DB: /tmp/qfa-ar-073.sqlite3; removed after run; durable raw daily paths/equity curves/weights retained: false.

## Primary metrics

| metric | pre-cost qfa | 5 bps | 10 bps |
|---|---:|---:|---:|
| Sharpe | -0.0837 | -0.2730 | -0.4576 |
| Ann. return | -0.0024 | -0.0073 | -0.0121 |
| Ann. vol | 0.0253 | 0.0255 | 0.0258 |
| Max drawdown | -0.0771 | -0.0906 | -0.1039 |
| Win rate | 0.4741 | 0.4721 | 0.4695 |

Primary annualized one-way turnover proxy at 10 bps basis: 9.6855x.

## Random/stress-window metrics (10 bps)

- Median Sharpe: -0.2121423
- p25 Sharpe: -1.4002676
- Worst Sharpe: -3.2215918
- Positive-window rate: 0.25
- Median annualized return: -0.0047914
- Median annualized volatility: 0.02413825
- Median win rate: 0.46746994
- Median annualized one-way turnover: 5.92144698x
- Worst max drawdown including primary: -0.10385991

## Orthogonality

Status: **limited_no_curves**

```json
{
  "attempted": true,
  "status": "limited_no_curves",
  "method": "Pearson correlation of AR-073 10 bps primary daily returns against retained latest.json equity curves for targeted AR-063/028/045/056/043/051 plus accepted/watchlist artifacts when available.",
  "comparisons": [
    {
      "alpha": "AR-045",
      "artifact": "models/closing-volume-reversal-costaware-megacap-v1/evaluations/latest.json",
      "status": "unavailable_no_retained_equity_curve"
    },
    {
      "alpha": "AR-028",
      "artifact": "models/closing-volume-reversal-megacap-v1/evaluations/latest.json",
      "status": "unavailable_no_retained_equity_curve"
    },
    {
      "alpha": "AR-056",
      "artifact": "models/closing-volume-reversal-orthogonalized-megacap-v1/evaluations/latest.json",
      "status": "unavailable_no_retained_equity_curve"
    },
    {
      "alpha": "AR-071",
      "artifact": "models/etf-realized-skew-crash-rebound-breadth-v1/evaluations/latest.json",
      "status": "unavailable_no_retained_equity_curve"
    },
    {
      "alpha": "AR-043",
      "artifact": "models/etf-stress-liquidity-volume-v1/evaluations/latest.json",
      "status": "unavailable_no_retained_equity_curve"
    },
    {
      "alpha": "AR-072",
      "artifact": "models/macro-drawdown-beta-redundancy-constrained-v1/evaluations/latest.json",
      "status": "unavailable_no_retained_equity_curve"
    },
    {
      "alpha": "AR-063",
      "artifact": "models/macro-surprise-drawdown-etf-allocator-v1/evaluations/latest.json",
      "status": "unavailable_no_retained_equity_curve"
    },
    {
      "alpha": "AR-051",
      "artifact": "models/xsec-etf-defensive-rotation-orthogonal-v1/evaluations/latest.json",
      "status": "unavailable_no_retained_equity_curve"
    }
  ],
  "max_abs_correlation_available": null
}
```

## Decision

**Suggested decision: rejected.** Rejected by falsifier: random-window Sharpe distribution, drawdown/turnover, or limited/high orthogonality evidence is not strong enough after 10 bps costs.

Suggested children are recorded in `latest.json`; no refinement child is proposed if rejected.
