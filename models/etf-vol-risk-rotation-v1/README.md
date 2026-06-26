# etf-vol-risk-rotation-v1

AR-035 evaluated a genuinely divergent volatility-regime ETF rotation mechanism. It does **not** use overnight gap reversal, opening imbalance, or a direct inversion/extension of AR-012.

## Mechanism

- Universe: SPY, QQQ, IWM, TLT, GLD, SLV, XLF, XLK, XLE, XLV.
- Regime features from completed daily OHLCV bars only:
  - 20-day versus 60-day realized-volatility pressure for SPY/QQQ/IWM;
  - 60-day positive-momentum breadth across the ETF universe;
  - 63-day SPY drawdown state; and
  - TLT/GLD defensive relative-strength alignment.
- Rotation:
  - risk-on candidates: SPY, QQQ, IWM, XLK, XLF, XLE, XLV;
  - defensive candidates: TLT, GLD, SLV, XLV;
  - candidates are ranked by trailing momentum divided by recent realized volatility and capped before qfa normalization.

## Evaluation constraints

- Data source: qfa AlpacaGateway real market data only.
- CSV usage: none; `--data-csv` was not used.
- Trading: no live trades, no daemon.
- DB handling: temporary SQLite DBs used by qfa and removed after JSON capture; no DB artifact retained.
- Costs/slippage: qfa backtest CLI has no native cost/slippage parameter. Evaluation artifacts document an ex-post 5 bps one-way turnover haircut proxy.

## Result

Suggested decision: **rejected**.

Primary qfa pre-cost Sharpe was 0.3053 with total return 19.34% and max drawdown -28.44%, but the 8-window random stability check had median Sharpe -0.1829. Approximate 5 bps cost-haircut Sharpe was 0.1237. Per bad-result policy, no refinement, direct inversion, or extension child was created.

See `evaluations/latest.json` and `evaluations/latest.md` for full metrics, command, qfa run ids, random-window results, cost proxy, and orthogonality checks.
