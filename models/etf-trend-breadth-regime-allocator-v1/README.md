# AR-077 — ETF trend-breadth regime allocator

Rule-based qfa research model using only Alpaca/qfa real daily OHLCV bars. The signal estimates cross-asset ETF trend breadth from 20/60/120-day returns, downside participation across risk ETFs on negative SPY days, SPY drawdown state, and inverse-volatility sizing.

## Universe

SPY, QQQ, IWM, TLT, IEF, SHY, GLD, XLU, XLE, XLV when available from Alpaca.

## Mechanism

- Risk-on: broad positive trend breadth and low downside participation allocate to equity/sector ETFs with defensive ballast.
- Transition: mixed breadth rotates toward a blend of positive-trend risk and defensive ETFs.
- Risk-off: weak breadth, drawdown, or high downside participation rotates to duration/cash/gold/utilities with a small equity stub only when drawdown is not severe.

## Evaluation controls

- Data: Alpaca/qfa real OHLCV only.
- CSV: no CSV source and no `--data-csv` argument.
- Execution: no daemon, no orders/trades.
- Costs: qfa native backtest metrics are pre-cost; evaluation applies an ex-post 5 bps one-way target-turnover haircut.
- Storage: temporary SQLite DB only; DB artifacts are removed after run.

Latest results: `evaluations/latest.md` and `evaluations/latest.json`.
