# Exact same-index ETF residual convergence v1

Research artifact for AR-133. The model trades only lagged log-close residual z-scores inside exact/near-identical benchmark ETF substitute clusters, long cheap residuals and short rich residuals, with next daily bar/next-close execution. Data access used configured paper-data access through qfa/Alpaca with values redacted. No CSV, daemon, orders, NAV, premium, or flow claims.

Decision: **rejected**.

Primary 10 bps full Sharpe: -0.96884879; random-window median/p25/worst Sharpe: -7.57522066 / -11.26252897 / -15.69415071; positive-window rate: 0.2.

See `evaluations/latest.json` and `evaluations/latest.md` for compact metrics.
