# AR-113 real-data evaluation — megacap-idiosyncratic-vol-normalization-v1

- Run: `ar113_qfa_alpaca_real_20260626T2206Z`
- Data: qfa/Alpaca real daily OHLCV, 2018-01-01 to 2026-06-26; no CSV, no data-csv, no daemon, no orders.
- Selected universe: AAPL, MSFT, NVDA, AMZN, META, GOOGL, AVGO, TSLA, JPM, LLY, XOM, UNH, COST, MA, V, JNJ, NFLX, AMD, CRM, ORCL, KO, SPY, XLK, XLY, XLC, XLF, XLV, XLE, XLP, XLI, XLU
- Primary 10 bps Sharpe: **-1.0107**; annualized return -0.021333; annualized vol 0.021114; max drawdown -0.125028.
- Turnover: 0.047242; activation days 208; opportunities 282.
- Random/stress windows: median Sharpe -1.1664, p25 -1.4272, worst -1.5534, positive rate 0.0.
- Cost sensitivity Sharpe: 5 bps -0.7302, 10 bps -1.0107, 20 bps -1.5638.
- Orthogonality max abs proxy correlation: 0.1746. Exact prior streams unavailable; proxy correlations retained in latest.json.
- Native qfa smoke: `qfa backtest run` against Alpaca real daily OHLCV, run ID 1 in temporary DB `/tmp/ar113_qfa_smoke.sqlite3`, 2023-01-03 to 2024-04-30, no CSV/no daemon/no orders; smoke Sharpe 0.9201 before external turnover-cost overlay.
- Suggested decision: **rejected**.

Warnings: Primary 10 bps Sharpe is negative.; Random/stress p25 Sharpe is negative.; 20 bps cost sensitivity is negative.
