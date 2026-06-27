# risk-off-crossasset-randomcost-v1

AR-025 refinement of AR-008. This model is a qfa-compatible, OHLCV-only liquid ETF regime switch evaluated with Alpaca real market data.

## Mechanism

- Risk-on bucket: SPY, QQQ, IWM, XLE.
- Risk-off bucket: TLT, GLD, XLU.
- Regime gate: 100-day equity trend/breadth, 40-day TLT/GLD relative strength versus SPY, and 20-day SPY realized-volatility throttle.
- Sizing: positive trailing momentum scaled by inverse realized volatility, capped before qfa gross normalization.

## Evaluation constraints

- Data source: qfa AlpacaGateway real market data only.
- CSV usage: none; `--data-csv` was not used.
- Trading: no live trades, no daemon.
- DB handling: temporary SQLite DBs used by qfa and removed after JSON capture; no DB artifact retained.
- Costs: qfa backtest CLI has no native cost/slippage parameter, so qfa metrics are pre-cost and the evaluation includes an ex-post 5 bps one-way turnover haircut estimate.

## Result

Suggested decision: **rejected**.

Primary qfa Sharpe was -0.0405, approximate 5 bps cost-haircut Sharpe was -0.1484, and 8-window median random qfa Sharpe was -0.2627. Per bad-result policy, no refinement/direct inversion/extension of the failed risk-off switch was created; AR-044 is a divergent child with a different credit/equity dispersion-reversion mechanism.

See `evaluations/latest.json` and `evaluations/latest.md` for full metrics.
