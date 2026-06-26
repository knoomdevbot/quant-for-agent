# AR-093 evaluation: crypto-stress-quality-flight-defensive-etf-allocator-v1

- Created: 2026-06-26T15:56:58Z
- Market data: Alpaca real daily OHLCV via qfa/AlpacaGateway only; no CSV and no `--data-csv`.
- External crypto data: Coinbase Exchange public candles JSON for BTC-USD and ETH-USD; raw arrays not retained; compact stress intervals embedded in `model.py`.
- Timestamp discipline: ETF signal date D uses BTC/ETH features shifted one completed UTC day (through D-1) and qfa applies weights to next ETF bar.
- Selected symbols: SPY, QQQ, IWM, TLT, IEF, SHY, GLD, HYG, LQD, XLU, XLP, XLV, USMV, QUAL
- qfa run IDs in temporary DB: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]; DB `/tmp/qfa-ar-093.sqlite3` removed after evaluation.

## Metrics (10 bps one-way turnover cost)

| Metric | Value |
|---|---:|
| Primary Sharpe | 0.5098 |
| Primary annualized return | 0.0417 |
| Primary annualized volatility | 0.0877 |
| Primary max drawdown | -0.2278 |
| Random-window median Sharpe | 0.3315 |
| Random-window p25 Sharpe | -0.3154 |
| Worst random-window Sharpe | -1.1821 |
| Positive-window rate | 0.5833 |
| Primary annualized one-way turnover | 11.2777x |

## Orthogonality

Status: **fail**; max available abs correlation: `0.61351759`.

## Decision

**Suggested decision: rejected.** Rejected by falsifier: random-window p25 Sharpe materially negative and/or median Sharpe not robust after costs; quality-flight response is unstable across inflation/rate regimes.

## Artifact policy

No raw equity curve, daily returns, weights, SQLite DB, cache, bytecode, or raw external crypto arrays retained. Immutable compact run: `models/crypto-stress-quality-flight-defensive-etf-allocator-v1/evaluations/runs/ar093_qfa_alpaca_coinbase_crypto_20260626T155658Z.json`.
