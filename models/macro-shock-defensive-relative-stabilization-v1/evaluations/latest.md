# AR-122 real-data evaluation: macro-shock defensive relative stabilization v1

Decision: **rejected**. Reject for watchlist: 10 bps median random-window Sharpe is negative or weak, positive-window rate below acceptance threshold, and shock-cluster hit rate/baseline dominance are insufficient after costs.

Data: Alpaca real daily OHLCV through qfa AlpacaGateway, 2020-01-02 to 2026-06-25; no CSV, no `--data-csv`, no daemon, no orders, no raw daily paths retained.

Selected universe fixed before performance review: SPY, QQQ, IWM, DIA, USMV, SPLV, QUAL, MTUM, XLK, XLY, XLP, XLV, XLU, XLF, XLI, XLE, XLB, XLRE, XLC, HYG, LQD, SHY, IEF, TLT, TIP, GLD, DBC.

## Key 10 bps metrics
- Full-period Sharpe -0.378108, annual return -0.030943, vol 0.081838, max drawdown -0.259145, total return -0.183773.
- Activation rate 0.340295; shock days 148 across 43 clusters.
- Random windows (10 bps): median Sharpe -0.418938, p25 -0.756965, worst -2.099422, positive Sharpe rate 0.25, worst MDD -0.209259.
- Cost stress Sharpe: 5 bps -0.155957; 10 bps -0.378108; 20 bps -0.807365.
- Shock cluster positive rate: 0.44186.
- Max abs proxy correlation: 0.799555.

## Warnings
- Proxy orthogonality only: existing compact alpha artifacts generally did not retain daily return series.
- Daily OHLCV-only macro-shock proxy, not external macro calendar.
- No raw bars/equity curves/daily returns/weights tails retained by design.
