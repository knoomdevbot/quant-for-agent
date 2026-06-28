# AR-131 latest evaluation

- Run: `ar131_qfa_alpaca_real_20260628T004057Z.json`
- Data/protocol: Alpaca/qfa real daily OHLCV; no CSV/`--data-csv`; no qfa daemon; no orders.
- qfa CLI smoke: 2024 real-data backtest (temporary `/tmp` SQLite deleted) Sharpe -2.06888019; total return -0.02148772; max DD -0.02323093; periods 250. Main event/cost study below uses a compact custom qfa/Alpaca evaluator for open-gap features and cost haircuts.
- Primary fade, 10 bps one-way: Sharpe -0.00406; ann return -0.000384; ann vol 0.024017; max drawdown -0.044644; turnover 0.0381; activation 0.100188; hit rate 0.342723; events 81.
- 5 bps sensitivity: Sharpe 0.196463; ann return 0.004428; max DD -0.036345.
- Random/event windows: median Sharpe -0.019324; p25 -0.697588; worst -1.523809; positive-window rate 0.454545 across 11 windows.
- Key ablations: shifted +5td Sharpe -0.84662; matched +21td Sharpe -0.573485; generic no-gate fade Sharpe -0.116406; generic no-gate continuation Sharpe -0.718958; AR-109 proxy Sharpe -1.880948; inflation-rotation proxy Sharpe -1.2264.
- Orthogonality: max available proxy daily-return corr 0.073222; exact accepted-stream correlations unavailable in compact retained artifacts.
- Decision suggestion: **rejected**.
