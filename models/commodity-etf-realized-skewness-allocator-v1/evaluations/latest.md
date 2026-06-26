# AR-111 evaluation: commodity ETF realized-skewness allocator

- Created: 2026-06-26T19:58:19Z
- Data source: Alpaca/qfa real daily OHLCV; no CSV; no `--data-csv`; no daemon; no orders.
- Candidate pool: GLD, SLV, USO, UNG, DBA, DBC, CPER, CORN, WEAT, SOYB, PALL, PPLT
- Selected primary universe: GLD, SLV, USO, UNG, DBA, DBC, CPER, CORN, WEAT, SOYB, PALL, PPLT
- Sector-equity proxies (`XLE, XOP, COPX`) are diagnostic only.
- Primary window: 2021-08-02 to 2025-12-31; random windows: 12.
- Compact artifact policy: no raw daily bars, equity curves, weights tails, SQLite DBs, caches, pyc, or helper evaluator scripts retained.

## Key metrics

| metric | value |
|---|---:|
| Primary Sharpe 10 bps | -0.4408 |
| Primary max drawdown 10 bps | -0.6772 |
| Primary annualized one-way turnover | 4.3172 |
| Random median Sharpe 10 bps | 0.1555 |
| Random p25 Sharpe 10 bps | -0.5652 |
| Random worst Sharpe 10 bps | -0.5887 |
| Positive random-window rate 10 bps | 0.5000 |
| Worst random max drawdown 10 bps | -0.6544 |

## Ablations

Pure commodity ETF-only is the primary result above. Expanded sector-equity proxy, no-energy, no-metals, long-only/underweight-high-skew, equal-weight and 12/18m lookback diagnostics are in `latest.json`; unavailable diagnostics are explicitly marked.

## Orthogonality

Simple proxy correlations vs DBC/GLD/USO/XLE/SPY/TLT are in `latest.json`. Prior alpha artifact correlations vs AR-097/AR-099/AR-101 are marked deferred where compact return series were not retained.

## Decision

**Suggested decision: rejected.** Rejected: 10 bps random-window median/p25 Sharpe and pure-commodity ETF proxy evidence do not satisfy robustness gates.
