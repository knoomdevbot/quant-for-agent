# CFTC COT positioning extreme-unwind ETF allocator v1

Research artifact for AR-135. The model exposes `generate_signals(context)` and is rejected after costed real-data evaluation.

## Hypothesis

Weekly CFTC Commitments of Traders positioning extremes and four-week changes, used only after public Friday release, may identify crowded futures exposures that unwind over the next 5-20 trading days in related U.S.-listed ETFs.

## Falsifier

Reject if the signal is stale/noisy, dominated by generic ETF momentum/reversal or position-only effects, fails costed random-window Sharpe/lower-tail gates, is too concentrated in a sleeve/regime, or is redundant with existing alpha artifacts.

## Data and universe

- ETF prices: real daily market bars via qfa AlpacaGateway only; no CSV price data and no `--data-csv`.
- External positioning: official CFTC public historical COT files fetched from cftc.gov and parsed in memory only; raw COT tables are not retained.
- Candidate pool: `GLD`, `SLV`, `USO`, `UNG`, `DBA`, `DBC`, `PDBC`, `GSG`, `TLT`, `IEF`, `SHY`, `TIP`, `UUP`, `FXE`, `FXY`, `SPY`, `QQQ`, `IWM`, `DIA`.
- Selected universe: `GLD`, `SLV`, `USO`, `UNG`, `TLT`, `IEF`, `UUP`, `SPY`, `QQQ`, `IWM`, selected for Alpaca coverage, liquidity proxy, and clean CFTC futures mapping.
- Release lag: Tuesday report date + Friday public release, traded no earlier than the next business day.

## Rule

Contrarian allocation opposite the crowded COT net-position z-score when `|z| >= 1.5` and either four-week COT change is already reversing or 20-day ETF momentum is not strongly confirming the crowded side. Per-symbol cap is 20%; gross cap is 100%.

## Evaluation summary

Primary cost is 10 bps per one-way turnover side, with 5/20 bps sensitivity. Random-window protocol used 30 deterministic pseudo-random subwindows.

- Primary 10 bps Sharpe: -0.1699
- Random median Sharpe: 0.0000
- Random p25 Sharpe: -0.5940
- Random worst Sharpe: -1.7069
- Positive-window rate: 0.4667
- Worst max drawdown: -0.1551
- Median annualized turnover: 12.9171x
- Orthogonality max available absolute correlation: 0.1060, limited to compact prior artifacts with retained equity curves.

Decision: **rejected**. Lower-tail robustness failed, positive-window rate was below 55%, and position-only/price-only/placebo controls were not convincingly beaten.

See `evaluations/latest.json` and `evaluations/latest.md` for full compact metrics.
