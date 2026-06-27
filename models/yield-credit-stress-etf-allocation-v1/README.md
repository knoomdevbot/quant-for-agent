# yield-credit-stress-etf-allocation-v1

AR-040 macro-regime ETF allocation model. The signal combines duration strength (TLT/IEF), gold strength (GLD), defensive-vs-cyclical sector relative performance, LQD-vs-HYG credit stress, equity breadth, and SPY realized volatility to shift long-only exposure between risk-on ETFs and Treasury/gold/defensive ETFs.

## qfa contract

`model.py` exposes `generate_signals(context)` and returns target weights for the configured symbols. The model uses only `context.prices` OHLCV bars supplied by qfa.

## Evaluation summary

Latest evaluation used real Alpaca data, no CSV, no daemon, and no trades. Primary post-cost proxy Sharpe was 0.1060; median random-window post-cost Sharpe was 0.4114; worst random-window drawdown was -0.2375. Suggested decision: **rejected**.

See `evaluations/latest.json` and `evaluations/latest.md` for full metrics, random windows, costs, and orthogonality checks.
