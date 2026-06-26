# AR-081 Evaluation — crossasset-volume-divergence-risk-transfer-v1

- Status: `completed_real_data_backtest`
- Decision: **reject** — Fails robustness threshold: p25 Sharpe/drawdown/orthogonality not adequate after turnover haircut.
- Data: Alpaca/qfa real daily OHLCV only; no CSV input; no daemon; no orders.
- qfa smoke run id: `1` (temporary SQLite removed)

## Primary after-cost metrics

| Metric | Value |
|---|---:|
| Annualized return | 0.02589457 |
| Annualized volatility | 0.06221603 |
| Max drawdown | -0.1676003 |
| Median window Sharpe | 0.45095645 |
| p25 window Sharpe | -0.65585534 |
| Worst window Sharpe | -1.61270531 |
| Positive window rate | 0.6 |
| Mean daily one-way turnover | 0.02633257 |

## Orthogonality

Max abs retained-library correlation: `None`; status `unavailable`.

## Suggested policy action

Reject; do not create refinement/direct extension. If more exploration is required, use the divergent child idea in latest.json.
