# AR-088 Evaluation: ETF realized-volatility asymmetry defensive allocator

- Created UTC: 2026-06-26T15:27:53Z
- Data: Alpaca/qfa real daily OHLCV only; no CSV; no `--data-csv`; no daemon; no orders.
- Symbols: SPY, QQQ, TLT, IEF, GLD, XLU, XLP, XLV, HYG, LQD, SHY
- Primary qfa run id: 1; random/stress qfa run ids: 2, 3, 4, 5, 6, 7, 8, 9, 10, 11
- Primary pre-cost Sharpe: 0.28745096; primary 10 bps cost-adjusted Sharpe: -0.05070501
- Random/stress 10 bps median Sharpe: 0.20576377; p25 Sharpe: -0.17351568; positive-window rate: 0.7; worst Sharpe: -1.22196659
- Orthogonality status: fail; max abs correlation: 0.90004171
- Suggested decision: **rejected** — Rejected by falsifier: cost-adjusted random-window p25 Sharpe <= 0 and/or robustness threshold not met.

Compact artifact policy: raw qfa equity curves, target weights, and raw daily bars are not retained; only aggregate metrics and run ids are retained. Temporary SQLite DB removed after evaluation.
