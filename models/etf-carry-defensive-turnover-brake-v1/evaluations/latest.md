# AR-060 Evaluation — etf-carry-defensive-turnover-brake-v1

## Decision

**REJECT** — Rejected: falsifier triggered by median random-window Sharpe <= 0, worse drawdown than AR-049, or orthogonality/performance hurdle.

## Data / execution

- Data source: Alpaca real daily OHLCV via qfa; no CSV and no `--data-csv`.
- Symbols: `SPY, QQQ, IWM, TLT, IEF, GLD, USO, FXE, FXY, UUP`.
- Primary: `2022-01-03` to `2025-12-15`. Random windows: `8` x `378` trading days.
- No daemon, no orders/trades. Temporary SQLite DB only; artifact retained: `false`.
- qfa CLI run id: `1`.

## Metrics

- Primary qfa/pre-cost Sharpe: `0.83123061`.
- Primary 5 bps cost-adjusted Sharpe: `0.80604468`.
- Primary 5 bps annualized return: `0.05082239`.
- Primary 5 bps max drawdown: `-0.08211551`.
- Primary 10 bps cost-adjusted Sharpe: `0.78083495`.
- Average daily turnover proxy: `0.01273247`; annualized turnover proxy: `3.20858173`.
- Random-window median/p25/worst 5 bps Sharpe: `-0.46117907` / `-0.75174613` / `-0.99350569`.
- Positive random-window rate: `0.25`.
- Worst random-window drawdown: `-0.09138622`.

## Orthogonality

- Max absolute retained-watchlist correlation: `0.91655861`.
- Passes ~0.60 threshold: `False`.

```json
[
  {
    "model_name": "AR-037_etf-carry-defensive-allocation-v1",
    "path": "/Users/moonk/quant-for-agent/models/etf-carry-defensive-allocation-v1/evaluations/latest.json",
    "status": "computed",
    "overlap_periods": 989,
    "correlation": 0.5478847
  },
  {
    "model_name": "AR-049_etf-carry-defensive-orthogonal-v1",
    "path": "/Users/moonk/quant-for-agent/models/etf-carry-defensive-orthogonal-v1/evaluations/latest.json",
    "status": "computed",
    "overlap_periods": 989,
    "correlation": 0.91655861
  },
  {
    "model_name": "AR-015_tsmom-voltarget-liquid-etf-randomcost-v1",
    "path": "/Users/moonk/quant-for-agent/models/tsmom-voltarget-liquid-etf-randomcost-v1/evaluations/latest.json",
    "status": "computed",
    "overlap_periods": 488,
    "correlation": 0.56237926
  }
]
```

## Artifacts

- Latest JSON: `/Users/moonk/quant-for-agent/models/etf-carry-defensive-turnover-brake-v1/evaluations/latest.json`
- Immutable run JSON: `/Users/moonk/quant-for-agent/models/etf-carry-defensive-turnover-brake-v1/evaluations/runs/ar060_qfa_alpaca_real_20260626T112748Z.json`
