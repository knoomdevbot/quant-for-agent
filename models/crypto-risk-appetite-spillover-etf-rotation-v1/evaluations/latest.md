# AR-092 Evaluation — crypto-risk-appetite-spillover-etf-rotation-v1

- Status: **rejected**
- Suggested decision: **rejected**
- Data: Alpaca real ETF daily OHLCV via qfa/AlpacaGateway; external BTC/ETH daily bars via Alpaca CryptoHistoricalDataClient. No CSV/no `--data-csv`; no daemon; no orders.
- Timestamp discipline: crypto daily features are effective only on the following calendar date; raw crypto/equity bars are not retained.
- Selected symbols: `QQQ, SPY, IWM, SMH, ARKK, HYG, LQD, TLT, IEF, SHY, GLD, XLE, XLU, XLV, XLP`
- Primary 10 bps cost-adjusted Sharpe: `-0.10725683`; annualized return `-0.01727774`; volatility `0.10798845`; max drawdown `-0.30469358`; turnover `0.16798792`.
- Random-window median/p25/worst Sharpe after costs: `0.35477704` / `0.08172428` / `-1.99136367`; positive-window rate `0.8`.
- qfa run IDs: primary `1`, random `[2, 3, 4, 5, 6, 7, 8, 9, 10, 11]`. Temporary DB deleted: `True`.

## Decision

Rejected: despite positive median/p25 random-window Sharpe, the full primary cost-adjusted Sharpe and annualized return are negative, max drawdown is about -30%, worst random-window Sharpe is severely negative (-1.99), and realized allocation overlaps existing ETF momentum/defensive rotation families.

## Warnings

- No trades, daemon, or orders were run.
- No raw Alpaca equity/crypto data, SQLite DB, caches, or bytecode retained in model artifacts.
