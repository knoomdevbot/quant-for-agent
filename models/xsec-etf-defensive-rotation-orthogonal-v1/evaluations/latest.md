# AR-051 evaluation: xsec-etf-defensive-rotation-orthogonal-v1

Created: 2026-06-26T10:27:24Z

## Result

Suggested decision: **watchlist_continue_research_not_accepted_due_to_orthogonality_and_tail_risk_uncertainty**

Main 2023-01-01..2025-12-31 qfa run id: `2`; smoke run id: `1`.

### Main metrics

| metric | pre-cost qfa | cost-adjusted 10bps | cost-adjusted 20bps |
|---|---:|---:|---:|
| Sharpe | 0.76142056 | 0.73029298 | 0.69905792 |
| Total return | 0.3050711 | 0.28967935 | 0.27445879 |
| Max drawdown | -0.17788804 | -0.17910946 | -0.18032998 |
| Ann. vol | 0.12832776 | 0.12833952 | 0.12837205 |

Turnover proxy: mean daily one-way `0.01581726`, median daily `0.0`, annualized `3.98594924`.

### Random windows (10bps one-way costs)

- Window count: 8
- Median Sharpe: 0.58872054
- p25 Sharpe: 0.24933382
- Worst Sharpe: 0.03111771
- Positive window rate: 1.0
- Worst max drawdown: -0.17910946
- Random qfa run ids: [3, 4, 5, 6, 7, 8, 9, 10]

### Orthogonality

[
  {
    "model": "tsmom-voltarget-liquid-etf-randomcost-v1",
    "artifact": "models/tsmom-voltarget-liquid-etf-randomcost-v1/evaluations/runs/qfa_real_alpaca_ar015_20260626T072547Z.json",
    "correlation": 0.62059549,
    "overlap_periods": 499
  },
  {
    "model": "etf-carry-defensive-allocation-v1",
    "artifact": "models/etf-carry-defensive-allocation-v1/evaluations/runs/ar037_qfa_alpaca_real_20260626T083545Z.json",
    "correlation": 0.61717278,
    "overlap_periods": 739
  },
  {
    "model": "xsec-etf-defensive-rotation-costmonthly-v1_parent_AR039",
    "status": "unavailable_no_overlap_or_no_equity_curve"
  }
]

Costs are not native in qfa; they were applied externally by replaying target weights. No daemon, no trades, no CSV input. Temporary DB `/tmp/qfa-AR-051-24295.sqlite3` was removed after artifact creation.

Immutable JSON: `models/xsec-etf-defensive-rotation-orthogonal-v1/evaluations/runs/ar051_qfa_alpaca_real_20260626T102756Z.json`
