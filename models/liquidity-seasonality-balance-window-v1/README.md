# liquidity-seasonality-balance-window-v1

Research artifact for AR-038. The model is a qfa-compatible `generate_signals(context)` alpha that is flat most days and holds a capped basket of highly liquid mega-cap equities around month-end/month-start and quarter-end/quarter-start balance-sheet windows.

- Data source for latest evaluation: Alpaca real daily OHLCV via qfa `AlpacaGateway`.
- CSV usage: none (`no_csv_used=true`; no `--data-csv`).
- Trading: research/backtest only; no daemon; no orders.
- Costs: latest evaluation applies a 5 bps one-way turnover haircut outside qfa because this repo version has no native cost/slippage argument.
- Latest decision: **rejected** - Rejected by falsifier: median random-period costed Sharpe -0.36843186 and worst random drawdown -0.19281088.

See `evaluations/latest.md` and `evaluations/latest.json` for metrics, qfa run ids, random windows, and command provenance.
