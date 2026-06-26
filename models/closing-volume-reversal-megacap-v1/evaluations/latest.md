# closing-volume-reversal-megacap-v1 (AR-028)

Status: **real-data evaluated; research watchlist, not trade-ready**.

## Mechanism

Genuinely divergent liquidity-reversal test from rejected AR-009. It does not use AR-009's multi-day price-pressure continuation signal and is not a direct inversion. It fades abnormal end-of-day pressure using daily close location near the bar high/low plus abnormal share/dollar volume.

Limitation: Alpaca/qfa daily bars do not expose closing-auction imbalance or auction-only volume; this is a documented close-location/abnormal-volume proxy.

## Primary qfa/Alpaca result

- Data: Alpaca real market data via qfa; no `--data-csv` and no CSV fixtures.
- Symbols: AAPL, MSFT, NVDA, AMZN, META, GOOGL, TSLA.
- Period: 2024-01-01 to 2025-12-31, 1Day.
- QFA run id: 1.
- DB: temporary `/tmp/qfa_ar028_1782461377_primary.sqlite3`, removed; `db_artifact_retained=false`.
- Sharpe: 0.86494464
- Total return: 0.47296142
- Max drawdown: -0.18727644
- Win rate: 0.126
- Periods: 500

## Random windows

- Count: 8
- Median Sharpe: 1.55112480
- Mean Sharpe: 1.62597036
- Positive Sharpe windows: 8/8
- Median total return: 0.27549945
- Worst max drawdown: -0.21813708

## Costs/slippage

Costs were not applied because qfa backtest CLI exposes no cost/slippage parameter. A 5 bps assumption is documented; all qfa metrics are pre-cost.

## Orthogonality

```json
{
  "status": "computed_against_rejected_parent_only",
  "note": "No complete accepted-alpha return stream registry was used in this pass; computed daily equity-return correlation versus rejected AR-009 parent for divergence context.",
  "comparison": "AR-009 volume-price-pressure-megacap-v1",
  "overlap_periods": 499,
  "daily_return_correlation": -0.4985744
}
```

## Suggested decision

Research watchlist only, not trade-ready: positive primary/random-window pre-cost results, but proxy quality and execution costs must be resolved before promotion.
