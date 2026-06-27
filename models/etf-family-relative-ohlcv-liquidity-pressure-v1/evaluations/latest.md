# AR-121 evaluation: ETF family-relative OHLCV liquidity-pressure v1

Decision suggestion: **rejected**. Fails AR-121 acceptance: median random-window Sharpe <= 0 or p25 materially negative / baselines not convincingly beaten.

Data: qfa/Alpaca real daily OHLCV, 2020-01-02 to 2026-06-18; no CSV, no `--data-csv`, no daemon, no orders. Selected 52/52 ETFs by ex-ante coverage/liquidity filters.

Primary all-history after warmup, 10 bps: Sharpe -5.115264, ann return -0.307033, max DD -0.887952, avg daily turnover 1.627019, activation 0.997992.

Random windows, 10 bps: median Sharpe -5.723, p25 -5.911, worst -6.417, positive-window rate 0.000. Cost stress median Sharpe: 5 bps -2.315597, 10 bps -5.723304, 20 bps -12.390098.

Baselines/ablations at 10 bps are in `latest.json`; max absolute proxy correlation 0.862731. Compact artifacts retain no raw bars, equity curves, daily returns, weights tails, DBs, caches, or helper scripts.
