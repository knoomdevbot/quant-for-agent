# AR-043: ETF stress liquidity-volume dislocation detector

## Summary

Watchlist alpha that uses Alpaca/qfa real daily OHLCV only. The model estimates cross-ETF liquidity stress from abnormal dollar volume, high-low range expansion, close-location value, and stress breadth, then shifts a long-only allocation between risk ETFs and defensive ETF sleeves.

This is intentionally not an overnight gap reversal and not a direct inversion of failed parent AR-026.

## Artifacts

- Model: `models/etf-stress-liquidity-volume-v1/model.py`
- Config: `models/etf-stress-liquidity-volume-v1/config.yaml`
- Metadata: `models/etf-stress-liquidity-volume-v1/metadata.yaml`
- Latest evaluation JSON: `models/etf-stress-liquidity-volume-v1/evaluations/latest.json`
- Latest evaluation Markdown: `models/etf-stress-liquidity-volume-v1/evaluations/latest.md`
- Immutable run JSON: `models/etf-stress-liquidity-volume-v1/evaluations/runs/ar043_qfa_alpaca_real_20260626T094720Z.json`

## Evaluation protocol

- Data source: Alpaca real OHLCV through qfa/AlpacaGateway.
- CSV usage: none; `--data-csv` was not used.
- Universe: SPY, QQQ, IWM, TLT, GLD, XLU, XLE.
- Primary period: 2021-01-04 to 2025-12-15.
- Random windows: 9 staggered/random windows.
- Costs: qfa has no native cost argument, so evaluation applied an ex-post 5 bps one-way turnover haircut.
- Daemon/orders: not used.

## Key metrics after cost proxy

- Primary Sharpe: 0.45490526
- Primary annualized return: 0.05663953
- Primary annualized volatility: 0.14444141
- Primary max drawdown: -0.17241563
- Random median Sharpe: 0.61968753
- Random p25 Sharpe: 0.12285326
- Worst random Sharpe: -0.25617409
- Positive random-window rate: 0.77777778
- Annualized turnover proxy: 18.54568264
- Max absolute correlation observed: 0.63661506

## Decision

Watchlist. Median and p25 random-window Sharpe are positive after the cost proxy, but the full-period Sharpe is modest, the worst random window is negative, max drawdown is material, and redundancy versus AR-008 is moderate.
