# AR-066 Evaluation — etf-realized-vol-carry-macrostress-v1

## Decision

**REJECT** — Rejected: p25 random-window Sharpe was materially negative and retained-watchlist correlation was high despite positive median random-window Sharpe.

## Data / execution

- Data source: Alpaca real daily OHLCV via qfa; no CSV and no `--data-csv`.
- Symbols: `SPY, QQQ, IWM, TLT, GLD, XLU, XLE, SHY`.
- Primary: `2021-01-04` to `2025-12-15`. Random windows: `10` x `378` trading days.
- No daemon, no orders/trades. Temporary SQLite DB only; artifact retained: `false`.
- qfa CLI run id: `1`.

## Metrics

- Primary qfa/pre-cost Sharpe: `0.13879093`.
- Primary 5 bps cost-adjusted Sharpe: `0.06369196`.
- Primary 5 bps annualized return: `0.00043262`.
- Primary 5 bps max drawdown: `-0.21827927`.
- Primary 10 bps cost-adjusted Sharpe: `-0.01138485`.
- Average daily turnover proxy: `0.06979817`; annualized turnover proxy: `17.58913871`.
- Random-window median/p25/worst 5 bps Sharpe: `0.40767835` / `-0.55796645` / `-0.81020671`.
- Positive random-window rate: `0.6`.
- Worst random-window drawdown: `-0.21541987`.

## Orthogonality

- Max absolute retained-watchlist correlation: `0.83598478`.
- Passes ~0.60 threshold: `False`.

```json
[
  {
    "model_name": "AR-053_post-macro-liquidity-vacuum-reversal-v1",
    "path": "/Users/moonk/quant-for-agent/models/post-macro-liquidity-vacuum-reversal-v1/evaluations/latest.json",
    "status": "insufficient_overlap",
    "overlap_periods": 0
  },
  {
    "model_name": "AR-021_turn-month-calendar-window-etf-v1",
    "path": "/Users/moonk/quant-for-agent/models/turn-month-calendar-window-etf-v1/evaluations/latest.json",
    "status": "insufficient_overlap",
    "overlap_periods": 0
  },
  {
    "model_name": "AR-042_macro-liquidity-flow-etf-v1",
    "path": "/Users/moonk/quant-for-agent/models/macro-liquidity-flow-etf-v1/evaluations/latest.json",
    "status": "insufficient_overlap",
    "overlap_periods": 0
  },
  {
    "model_name": "AR-043_etf-stress-liquidity-volume-v1",
    "path": "/Users/moonk/quant-for-agent/models/etf-stress-liquidity-volume-v1/evaluations/latest.json",
    "status": "computed",
    "overlap_periods": 1241,
    "correlation": 0.83565239
  },
  {
    "model_name": "watchlist_AR-015_tsmom-voltarget-liquid-etf-randomcost-v1",
    "path": "/Users/moonk/quant-for-agent/models/tsmom-voltarget-liquid-etf-randomcost-v1/evaluations/latest.json",
    "status": "computed",
    "overlap_periods": 488,
    "correlation": 0.49711731
  },
  {
    "model_name": "watchlist_AR-037_etf-carry-defensive-allocation-v1",
    "path": "/Users/moonk/quant-for-agent/models/etf-carry-defensive-allocation-v1/evaluations/latest.json",
    "status": "computed",
    "overlap_periods": 989,
    "correlation": 0.65485917
  },
  {
    "model_name": "watchlist_AR-055_etf-stress-recovery-halflife-v1",
    "path": "/Users/moonk/quant-for-agent/models/etf-stress-recovery-halflife-v1/evaluations/latest.json",
    "status": "computed",
    "overlap_periods": 1241,
    "correlation": 0.83598478
  },
  {
    "model_name": "watchlist_AR-059_etf-defensive-momentum-carry-rotation-v1",
    "path": "/Users/moonk/quant-for-agent/models/etf-defensive-momentum-carry-rotation-v1/evaluations/latest.json",
    "status": "insufficient_overlap",
    "overlap_periods": 0
  }
]
```

## Artifacts

- Latest JSON: `/Users/moonk/quant-for-agent/models/etf-realized-vol-carry-macrostress-v1/evaluations/latest.json`
- Immutable run JSON: `/Users/moonk/quant-for-agent/models/etf-realized-vol-carry-macrostress-v1/evaluations/runs/ar066_qfa_alpaca_real_20260626T121321Z.json`
