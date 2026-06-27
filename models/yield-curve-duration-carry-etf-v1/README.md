# AR-061 — yield-curve-duration-carry-etf-v1

Research alpha for AOI/QFA. The model is a weekly-rebalanced, long-only ETF allocator using only daily OHLCV bars supplied by qfa/Alpaca. It focuses on ETF-implied curve and duration behavior rather than AR-049's broader OHLCV carry/defensive rotation.

## Universe

`SHY`, `IEF`, `TLT`, `TIP`, `LQD`, `HYG`, `GLD`, `SPY`.

## Signal outline

- Duration trend/carry proxy: relative performance of `TLT`/`SHY`, `IEF`/`SHY`, and `TLT`/`IEF`.
- Inflation proxy: `TIP` vs `IEF` plus `GLD` trend.
- Credit stress proxy: `LQD` vs `HYG` and `IEF` vs `HYG`.
- Risk controls: SPY drawdown, TLT/IEF realized volatility, cash residual, single-name caps, capped credit sleeve.

## Evaluation contract

Artifacts are in `evaluations/latest.json`, `evaluations/latest.md`, and immutable `evaluations/runs/*.json`. Evaluation uses Alpaca real market data via qfa only; CSV input and `--data-csv` are not used. No daemon, no orders, no trades.
