# crossasset-realized-correlation-breakdown-allocator-v1

Research artifact for AR-080: divergent child of AR-072 testing whether realized cross-asset correlation breakdowns identify distinct allocation regimes.

## Model

`model.py` exposes `generate_signals(context)` and uses only OHLCV bars supplied by qfa/Alpaca. It computes rolling stock/bond, credit/equity, and gold/equity correlations and z-scores, combines those with equity volatility/drawdown and breadth, then allocates long-only across SPY, QQQ, TLT, IEF, GLD, XLU, XLP, XLV, HYG, LQD, and SHY. Gross exposure is capped at 1.0 and single ETF weight at 0.34.

## Evaluation

- Data: Alpaca real daily bars through qfa/AlpacaGateway only; no CSV and no data-csv argument.
- Primary qfa window: 2021-01-04 to 2025-12-15; run id `1` in a temporary SQLite DB removed after evaluation.
- Cost proxy: 5 bps one-way times daily target-weight turnover.

## Summary metrics (5 bps cost-adjusted unless noted)

| metric | value |
|---|---:|
| median random-window Sharpe | 0.0 |
| p25 random-window Sharpe | -0.8103479 |
| worst random-window Sharpe | -1.19800957 |
| primary annualized return | -0.00252675 |
| primary annualized volatility | 0.07110019 |
| primary max drawdown | -0.2199614 |
| turnover proxy | 64.78318122 |
| positive window rate | 0.44444444 |
| max available orthogonality correlation | 0.76185761 |

## Decision

**REJECT** — Rejected: random-window p25 Sharpe was negative and/or max available retained-curve correlation breached 0.60.

See `evaluations/latest.json`, `evaluations/latest.md`, and immutable run JSON `ar080_qfa_alpaca_real_20260626T140814Z.json`.
