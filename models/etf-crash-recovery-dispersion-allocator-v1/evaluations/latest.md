# AR-064 evaluation: etf-crash-recovery-dispersion-allocator-v1

- Created: 2026-06-26T12:11:28Z
- Data: Alpaca real market data via qfa AlpacaGateway; no CSV; no `--data-csv`; no daemon; no orders.
- Symbols: SPY, QQQ, IWM, XLV, XLU, XLP, XLE, TLT, IEF, GLD
- Primary window: 2020-01-01 to 2025-12-31; random/stress windows: 10.
- Temporary qfa SQLite DB: `/tmp/qfa-ar064-backtests.sqlite3`; deleted: True; qfa run IDs: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11].
- Cost proxy: external one-way turnover haircut at 10 bps and 20 bps.

## Primary metrics

| metric | pre-cost qfa | 10 bps | 20 bps |
|---|---:|---:|---:|
| Sharpe | -0.2560 | -0.6018 | -0.9443 |
| Ann. return | -0.0525 | -0.1031 | -0.1510 |
| Ann. vol | 0.1577 | 0.1581 | 0.1587 |
| Max drawdown | -0.3597 | -0.4875 | -0.6260 |
| Win rate | 0.4681 | 0.4522 | 0.4376 |

Primary annualized one-way turnover proxy: 54.7588x.

## Random-window metrics (10 bps)

- Median Sharpe: -0.51296081
- p25 Sharpe: -1.13917327
- Worst Sharpe: -2.16554085
- Positive-window rate: 0.2
- Worst max drawdown including primary: -0.48752063
- Median annualized one-way turnover: 55.12666103x

## Orthogonality

```json
{
  "attempted": true,
  "method": "Pearson correlation of AR-064 10 bps cost-adjusted primary daily returns vs retained artifact equity-curve daily returns.",
  "comparisons": [
    {
      "alpha": "AR-050",
      "status": "unavailable_no_equity_curve",
      "artifact": "models/etf-convexity-stress-premium-v1/evaluations/latest.json"
    },
    {
      "alpha": "AR-043",
      "status": "unavailable_no_equity_curve",
      "artifact": "models/etf-stress-liquidity-volume-v1/evaluations/latest.json"
    },
    {
      "alpha": "AR-037",
      "status": "unavailable_no_equity_curve",
      "artifact": "models/etf-carry-defensive-allocation-v1/evaluations/latest.json"
    },
    {
      "alpha": "AR-051",
      "artifact": "models/xsec-etf-defensive-rotation-orthogonal-v1/evaluations/latest.json",
      "correlation": 0.15047784,
      "overlap_periods": 248
    }
  ],
  "max_abs_correlation_available": 0.15047784
}
```

## Decision

**Suggested decision: rejected.** Rejected by falsifier: random-window robustness after turnover costs and/or drawdown/orthogonality threshold was insufficient.

Bad-result policy followed: no refinement/direct inversion/extension child is suggested.  The JSON records at most one genuinely divergent child.
