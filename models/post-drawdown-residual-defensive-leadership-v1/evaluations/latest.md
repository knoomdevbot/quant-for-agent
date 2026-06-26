# AR-107 evaluation: post-drawdown residual defensive leadership

- Created: 2026-06-26T17:49:03Z
- Data: qfa/Alpaca real daily market data only; no CSV, no `--data-csv`, no daemon, no orders.
- Universe: 119 fixed ex-ante large-cap single names + SPY + 11 sector ETF proxies.
- Primary: 2020-01-01 to 2026-06-18; random/stress windows: 12.

## Primary metrics

| metric | pre-cost | 5 bps | 10 bps | 20 bps |
|---|---:|---:|---:|---:|
| Sharpe | 0.0901 | 0.0226 | -0.0449 | -0.1800 |
| Ann. return | 0.0036 | -0.0004 | -0.0045 | -0.0125 |
| Max DD | -0.1205 | -0.1241 | -0.1288 | -0.1418 |

Annualized turnover: 8.0969x; activation: 0.1486; mean/max sector concentration: 0.0351/0.2840.

## Random-window 10 bps summary
- Median Sharpe: -0.02304834
- p25 Sharpe: -0.50824911
- Worst Sharpe: -1.93476865
- Positive-window rate: 0.5
- Worst max DD: -0.12879694
- Median turnover: 12.81530552x; median activation: 0.24930844

## Attribution and orthogonality
Residual-only 10 bps Sharpe: -0.1357; defensive-only 10 bps Sharpe: 0.1308. Full-score median Spearman to residual score: 0.97431027; to defensive score: 0.17198655.

Max available absolute correlation to retained alphas/proxies: 0.3779.

## Decision
**REJECTED** — Rejected: 10 bps random-window median Sharpe <= 0; 10 bps random-window p25 Sharpe < 0; 20 bps primary Sharpe non-positive.
