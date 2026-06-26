# AR-069 Evaluation — post-gap-residual-continuation-megacap-v1

**Suggested decision:** `rejected` — Falsifier tripped: median random-window Sharpe <= 0, primary Sharpe <= 0, or peer correlation > 0.50 after cost adjustment.

## Data / safety
- Alpaca/qfa real daily OHLCV only; no CSV and no `--data-csv`.
- No daemon and no orders. Temporary DB `/tmp/qfa-AR-069-eval.sqlite3` was used during evaluation and removed after the run.
- Raw daily paths/equity curves are not retained in durable artifacts (`raw_daily_paths_retained: false`).
- Primary window: 2024-01-01 to 2025-12-31; random/stress windows: 8.
- Immutable run JSON: `/Users/moonk/quant-for-agent/models/post-gap-residual-continuation-megacap-v1/evaluations/runs/ar069_qfa_alpaca_real_20260626T124127Z.json`.

## Metrics (5 bps one-way turnover haircut)
- Primary Sharpe: `-0.7400`; annualized return: `-0.1115`; annualized vol: `0.1455`; max drawdown: `-0.2824`.
- Primary annualized turnover proxy: `90.4861`; active periods: `372`.
- Random median Sharpe: `-0.2764`; p25 Sharpe: `-1.0204`; worst-period Sharpe: `-1.8315`.
- Positive-window rate: `37.50%`; worst random drawdown: `-0.3063`.

## Orthogonality
```json
[
  {
    "model": "AR-056 closing-volume-reversal-orthogonalized-megacap-v1",
    "status": "computed_same_alpaca_bars",
    "daily_cost_adjusted_return_correlation": 0.02547882,
    "overlap_periods": 500
  },
  {
    "model": "AR-045 closing-volume-reversal-costaware-megacap-v1",
    "status": "computed_same_alpaca_bars",
    "daily_cost_adjusted_return_correlation": 0.05883407,
    "overlap_periods": 500
  },
  {
    "model": "AR-028 closing-volume-reversal-megacap-v1",
    "status": "computed_same_alpaca_bars",
    "daily_cost_adjusted_return_correlation": -0.03539139,
    "overlap_periods": 500
  },
  {
    "model": "SPY proxy",
    "status": "computed_same_alpaca_bars",
    "daily_return_correlation": -0.08581583,
    "overlap_periods": 500
  },
  {
    "model": "mega-cap equal-weight proxy",
    "status": "computed_same_alpaca_bars",
    "daily_return_correlation": -0.0476674,
    "overlap_periods": 500
  }
]
```

## QFA run ids
```json
{
  "primary_cli": 1,
  "primary_direct_stored_temp_db": 1,
  "random_windows_direct_stored_temp_db": [
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9
  ]
}
```
