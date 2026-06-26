# low-vol-quality-proxy-megacap-v1

AR-010 research model: long-only defensive-factor proxy inside mega-cap equities.

## Hypothesis
Lower realized volatility plus positive intermediate momentum may proxy for quality/defensive demand and produce improved risk-adjusted returns versus unconstrained mega-cap exposure.

## Model
- Universe: AAPL, MSFT, NVDA, AMZN, META, GOOGL, TSLA, JNJ, PG, KO, PEP, WMT.
- Compute 126-day realized volatility from adjusted closes.
- Keep names with positive 126-day total return.
- Select the 6 lowest-volatility names, inverse-vol weighted.
- Gross exposure <= 1.0; single-name cap 20%; long-only.

## Evaluation
Primary evaluation used qfa with Alpaca real market data only. No `--data-csv`, no CSV fixtures, no trades, and no qfa daemon.

See:
- `evaluations/latest.json`
- `evaluations/latest.md`
- `evaluations/runs/qfa_real_alpaca_20260626T063544Z.json`

## Result
Watchlist: full-period pre-cost Sharpe 0.35445852 with annualized return 0.03414158 and max drawdown -0.16939658. Random 30-window median Sharpe was 0.08598409 with positive-Sharpe fraction 0.5.

Costs/slippage were not applied by qfa; current qfa CLI has no cost/slippage parameter.
