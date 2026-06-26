# AR-079 Evaluation — intraday-range-expansion-close-location-reversal-breadth-v1

- Status: `completed_bounded_real_intraday`
- Decision: **reject** — Bounded real 1Min test fails robustness/activation threshold after 10 bps turnover haircut.
- Data: Alpaca/qfa real 1Min OHLCV only; no CSV input; no daemon; no orders.
- qfa 1Min smoke: `completed`, run id `1`, temporary SQLite removed `True`.

## Primary after-cost metrics

| Metric | Value |
|---|---:|
| Annualized return | -0.99937096 |
| Annualized volatility | 0.05784154 |
| Max drawdown | -0.06534504 |
| Median window Sharpe | -116.90279197 |
| p25 window Sharpe | -120.40634566 |
| Worst window Sharpe | -127.4060536 |
| Positive window rate | 0.0 |
| Mean one-way turnover/bar | 0.07564611 |

## Notes

This is a short bounded recovery evaluation on real intraday data. It is not a daily proxy and omits equity curves/raw bars from retained artifacts. Orthogonality correlation is unavailable because comparable retained intraday curves were not found.

## Suggested policy action

Reject; do not create refinement/direct extension. If more exploration is required, use only the divergent child idea in latest.json.
