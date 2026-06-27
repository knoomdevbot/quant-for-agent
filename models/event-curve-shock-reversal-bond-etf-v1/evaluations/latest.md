# AR-070 evaluation: event-curve-shock-reversal-bond-etf-v1

**Decision:** reject.

## What was run
- Real Alpaca daily OHLCV via qfa CLI; no CSV / no `--data-csv`.
- Temporary SQLite DB: `/tmp/qfa-ar-070.sqlite3` (removed after artifact generation).
- No daemon and no orders.
- Universe: SHY, IEF, TLT, TIP, LQD, HYG, GLD, SPY.
- Primary range: 2022-01-03 to 2025-12-15.

## Key results
- Primary pre-cost Sharpe: -0.53422534; total return: -0.10871806.
- Primary 5 bps cost-adjusted Sharpe: -0.92768679; total return: -0.17795824; max drawdown: -0.21873719.
- Primary 10 bps cost-adjusted Sharpe: -1.316767; total return: -0.24185061.
- Median random-window Sharpe at 5 bps: -0.63122956 (positive-window rate 0.0).
- Event-year windows: [{'name': 'y2022', 'start': '2022-01-03', 'end': '2022-12-30', 'qfa_run_id': 2, 'sharpe_5bps': -0.82586383, 'total_return_5bps': -0.04309238}, {'name': 'y2023', 'start': '2023-01-03', 'end': '2023-12-29', 'qfa_run_id': 3, 'sharpe_5bps': -0.92029381, 'total_return_5bps': -0.04119162}, {'name': 'y2024', 'start': '2024-01-02', 'end': '2024-12-31', 'qfa_run_id': 4, 'sharpe_5bps': -1.58967253, 'total_return_5bps': -0.05504415}, {'name': 'y2025', 'start': '2025-01-02', 'end': '2025-12-15', 'qfa_run_id': 5, 'sharpe_5bps': 0.41821937, 'total_return_5bps': 0.00853626}].
- Orthogonality status: computed where retained curves were available; max absolute retained-curve correlation 0.61499481.

## Interpretation
The event-gated daily-bar hypothesis failed its falsifier: cost-adjusted primary Sharpe is negative and the median random window is negative. Results are also year-concentrated: 2025 is positive while 2022-2024 event-year slices are negative. The model is distinct from AR-061 in construction, but standalone performance is not acceptable.

## Suggested next step
No refinement/extension child because the result is rejected. At most one divergent child: test intraday post-announcement Treasury ETF mean reversion with explicit announcement timestamps and intraday bars if permitted; otherwise block.
