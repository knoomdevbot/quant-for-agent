# AR-101 — Commodity inflation-shock cross-asset ETF rotation

Rule-based qfa allocator using Alpaca/qfa daily OHLCV only. The model watches commodity, precious-metal, credit, duration, and sector ETF behavior to infer inflation/liquidity shock regimes, then rotates long-only weights across commodity-sensitive ETFs, defensive sectors, duration/credit, and broad equity risk.

## Universe

`SPY, QQQ, IWM, XLE, XLB, XLI, XLF, XLV, XLP, XLU, GLD, SLV, USO, DBC, DBA, TIP, TLT, IEF, SHY, HYG, LQD`

## Signal summary

- Commodity impulse: 5/21-day returns across USO/DBC/DBA/GLD/SLV/XLE/XLB plus commodity volatility expansion.
- Inflation/stagflation state: commodity trend, duration pressure, credit-vs-duration confirmation, and equity trend.
- Rotation sleeves: commodity cyclicals, precious/TIP, defensive sectors, duration/credit, and risk assets.
- Risk: long-only, gross <= 1, max single ETF weight 25%, SHY/cash-like exposure via residual uninvested capital.

## Data and evaluation policy

Evaluations use Alpaca real daily market data through qfa interfaces only. No CSV-backed data, no data CSV argument, no qfa daemon, and no orders/trades. Durable artifacts intentionally omit raw daily data, path-level portfolio records, caches, SQLite DBs, and credential snippets.

## Latest decision

Rejected after one smoke window plus nine random/stress real-data windows. At a 10 bps one-way turnover-cost proxy the median Sharpe was 0.179, p25 Sharpe was -0.480, worst Sharpe was -0.491, worst max drawdown was -20.9%, mean average daily turnover was 0.099, and the 20 bps median Sharpe turned negative. No refinement/direct-extension child is proposed.
