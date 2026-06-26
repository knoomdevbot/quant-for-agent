# AR-061 Evaluation — yield-curve-duration-carry-etf-v1

## Decision

**REJECT** — Rejected: fails positive primary/random-window hurdle or retained-library orthogonality hurdle after costs.

## Data / execution

- Data source: Alpaca real daily OHLCV via qfa; no CSV and no `--data-csv`.
- Symbols: `SHY, IEF, TLT, TIP, LQD, HYG, GLD, SPY`.
- Primary: `2022-01-03` to `2025-12-15`. Random windows: `10` x `378` trading days.
- No daemon, no orders/trades. Temporary SQLite DB only; artifact retained: `false`.
- qfa CLI run id: `1`.

## Metrics

- Primary qfa/pre-cost Sharpe: `0.46045618`.
- Primary 5 bps cost-adjusted Sharpe: `0.41368563`.
- Primary 5 bps annualized return / vol: `0.02434071` / `0.06291532`.
- Primary 5 bps max drawdown / win rate: `-0.09954264` / `0.40606061`.
- Primary 10 bps cost-adjusted Sharpe: `0.36690303`.
- Average daily turnover proxy: `0.02331416`; annualized turnover proxy: `5.87516752`.
- Random-window median/mean/p25/worst/best 5 bps Sharpe: `0.44419568` / `0.31558466` / `0.08501924` / `-0.57140893` / `1.0494768`.
- Positive random-window rate: `0.8`.
- Worst random-window drawdown: `-0.09327109`.

## Orthogonality

- Status: `computed_where_retained_curves_available`.
- Max absolute retained-watchlist correlation: `0.92501061`.
- Passes ~0.60 threshold: `False`.

```json
[
  {
    "model_name": "AR-008_risk-off-crossasset-switch-v1",
    "path": "/Users/moonk/quant-for-agent/models/risk-off-crossasset-switch-v1/evaluations/latest.json",
    "status": "computed",
    "overlap_periods": 488,
    "correlation": 0.39056646
  },
  {
    "model_name": "AR-015_tsmom-voltarget-liquid-etf-randomcost-v1",
    "path": "/Users/moonk/quant-for-agent/models/tsmom-voltarget-liquid-etf-randomcost-v1/evaluations/latest.json",
    "status": "computed",
    "overlap_periods": 488,
    "correlation": 0.44056406
  },
  {
    "model_name": "AR-037_etf-carry-defensive-allocation-v1",
    "path": "/Users/moonk/quant-for-agent/models/etf-carry-defensive-allocation-v1/evaluations/latest.json",
    "status": "computed",
    "overlap_periods": 989,
    "correlation": 0.53590116
  },
  {
    "model_name": "AR-049_etf-carry-defensive-orthogonal-v1",
    "path": "/Users/moonk/quant-for-agent/models/etf-carry-defensive-orthogonal-v1/evaluations/latest.json",
    "status": "computed",
    "overlap_periods": 989,
    "correlation": 0.85740329
  },
  {
    "model_name": "AR-060_etf-carry-defensive-turnover-brake-v1",
    "path": "/Users/moonk/quant-for-agent/models/etf-carry-defensive-turnover-brake-v1/evaluations/latest.json",
    "status": "computed",
    "overlap_periods": 989,
    "correlation": 0.92501061
  }
]
```

## Suggested children

```json
[
  {
    "type": "divergent",
    "title": "Macro announcement curve-shock reversal using scheduled FOMC/CPI dates if qfa later supports event calendars"
  }
]
```

## Artifacts

- Latest JSON: `/Users/moonk/quant-for-agent/models/yield-curve-duration-carry-etf-v1/evaluations/latest.json`
- Immutable run JSON: `/Users/moonk/quant-for-agent/models/yield-curve-duration-carry-etf-v1/evaluations/runs/ar061_qfa_alpaca_real_20260626T115657Z.json`
