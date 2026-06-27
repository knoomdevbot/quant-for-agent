# bond-etf-carry-vol-regime-allocator-v1

AR-086 qfa-compatible research alpha using daily bond ETF term-structure carry proxies, credit-duration relative strength, and realized-volatility/drawdown regime brakes across SHY, IEF, TLT, TIP, LQD, HYG, GLD, and SPY.

## Signal

- Duration sleeve ranks IEF/TLT/TIP by medium/slow trend versus SHY, volatility, and drawdown.
- Credit sleeve ranks LQD/HYG versus IEF and suppresses exposure during equity/credit stress.
- GLD/SPY diversifier sleeve is small; SHY absorbs residual defensive allocation.

## Evaluation summary

Suggested decision: **rejected**

Primary 2021-2025 5 bps Sharpe: `0.00836755`, annualized return: `-0.00131945`, max drawdown: `-0.19376816`.
Random/stress windows (12) median Sharpe: `-0.24134084`, p25 Sharpe: `-0.84694713`, worst Sharpe: `-1.38871688`, positive-window rate: `0.33333333`.

Controls: no CSV, no `--data-csv`, no daemon, no orders. Compact artifacts omit raw daily paths, equity curves, and weight tails.

See `evaluations/latest.json` and `evaluations/latest.md` for full compact results.
