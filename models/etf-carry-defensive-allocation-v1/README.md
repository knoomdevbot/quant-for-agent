# etf-carry-defensive-allocation-v1

AR-037 qfa-compatible liquid ETF allocation using Alpaca real OHLCV only. The model allocates among SPY, QQQ, IWM, TLT, IEF, GLD, USO, FXE, FXY, and UUP using slow cross-asset carry/defensive proxies, volatility risk budgeting, and sleeve caps. It deliberately differs from pure price TSMOM by using defensive regime gates, relative carry/stability scores, and cash residuals.

## Research constraints

- qfa/Alpaca real market data only.
- No CSV and no `--data-csv`.
- No daemon and no live trades.
- Temporary SQLite DBs are removed after retaining JSON artifacts.

## Latest result

See `evaluations/latest.json` and `evaluations/latest.md`. Suggested decision: **watchlist_not_accepted**.
