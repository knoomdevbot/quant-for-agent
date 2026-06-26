# commodity-etf-realized-skewness-allocator-v1

AR-111 tests the Quantpedia/source-paper inspired commodity skewness hypothesis using qfa-compatible Alpaca real daily data and a fixed ex-ante ETF/ETN proxy universe.

## Hypothesis

Commodity-linked ETFs/ETNs with lower lagged 12-month realized daily-return skewness should outperform higher-skewness, lottery-like commodity exposures on a monthly cross-sectional basis.

## Primary universe

Fixed before evaluation: `GLD`, `SLV`, `USO`, `UNG`, `DBA`, `DBC`, `CPER`, `CORN`, `WEAT`, `SOYB`, `PALL`, `PPLT` subject only to Alpaca data availability/history filters. Sector-equity commodity proxies (`XLE`, `XOP`, `COPX`) are diagnostic-only.

## Signal

- Monthly stateless qfa rebalance anchor at first available trading day of each month.
- Compute 252-trading-day realized skewness of daily returns with at least 210 observations.
- Long lowest-skewness tercile, short highest-skewness tercile.
- Equal-vol weighting inside long/short buckets, gross <= 1, max absolute single-symbol weight 20%.

## Evaluation policy

Artifacts use Alpaca/qfa real market data only: no CSV, no `--data-csv`, no daemon, no orders. Evaluation artifacts are compact: no raw daily bars, raw equity curves, weights tails, SQLite DBs, caches, helper scripts, pyc, or `__pycache__` are retained.
