# AR-058 Evaluation — liquidity-exhaustion-recovery-regimegated-megacap-v1

**Suggested decision:** `rejected` — Falsifier tripped: median random-window Sharpe <= 0 after 5 bps turnover haircut or positive windows <= 50%.

## Data / safety
- Alpaca/qfa real daily data only; no CSV and no `--data-csv`.
- No daemon and no orders. Temporary DB `/tmp/qfa-AR-058-primary-32141.sqlite3` was used during evaluation and is not retained.
- Primary window: 2024-01-01 to 2025-12-31; random/stress windows: 8 including 2020 and 2022.
- Immutable run JSON: `/Users/moonk/quant-for-agent/models/liquidity-exhaustion-recovery-regimegated-megacap-v1/evaluations/runs/ar058_qfa_alpaca_real_20260626T112811Z.json`.

## Metrics (5 bps one-way turnover haircut)
- Primary Sharpe: `0.0234`; total return: `0.0005`; max drawdown: `-0.0162`.
- Primary annualized turnover proxy: `1.0080`; active periods: `3`.
- Random median Sharpe: `0.0000`; p25 Sharpe: `0.0000`; worst Sharpe: `0.0000`.
- Positive-window rate: `12.50%`; worst random drawdown: `-0.0007`.
- AR-046 parent primary Sharpe: `0.8068`; parent max drawdown: `-0.0491`; parent annualized turnover: `10.0800`.

## Orthogonality
[
  {
    "model": "AR-046 parent",
    "daily_cost_adjusted_return_correlation": 0.02446036,
    "overlap_periods": 500
  },
  {
    "model": "AR-028 closing-volume-reversal-megacap-v1",
    "daily_cost_adjusted_return_correlation": 0.04928242,
    "overlap_periods": 500
  },
  {
    "model": "AR-045 closing-volume-reversal-costaware-megacap-v1",
    "daily_cost_adjusted_return_correlation": 0.10554391,
    "overlap_periods": 500
  },
  {
    "model": "SPY proxy",
    "daily_return_correlation": 0.05197736,
    "overlap_periods": 500
  },
  {
    "model": "mega-cap equal-weight proxy",
    "daily_return_correlation": 0.05771137,
    "overlap_periods": 500
  }
]
