# AR-089 evaluation: cross-asset overnight gap absorption allocator

- Created: 2026-06-26T15:36:15Z
- Data: Alpaca/qfa real daily OHLCV, 2018-01-01 to 2025-12-31; no CSV, no data-csv flag, no daemon, no orders.
- Temporary SQLite retained: false
- Primary window: 2021-01-04 to 2025-12-15
- Primary qfa pre-cost Sharpe: 0.28009224
- Primary 10 bps cost-adjusted Sharpe: -0.96874576; annualized return: -0.05448804; max drawdown: -0.24319368
- Random/stress windows: 6; median Sharpe (10 bps): -0.7971498; p25 Sharpe: -1.14918612; positive-window rate: 0.33333333
- Orthogonality status: pass; max abs comparator correlation: 0.34175357
- Suggested decision: **rejected**

## Notes
Daily bars approximate overnight/open-to-close absorption only after the session close, so the qfa backtest targets the next session and may miss true open execution dynamics. External turnover haircuts of 5/10/20 bps one-way were applied; qfa native metrics are pre-cost. Raw daily records, equity curves, and weight tails were not retained.

Immutable run JSON: `evaluations/runs/ar089_qfa_alpaca_real_20260626T153615Z.json`
