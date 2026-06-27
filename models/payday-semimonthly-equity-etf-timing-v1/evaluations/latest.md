# AR-110 Evaluation Result — qfa/Alpaca real data

- Created: 2026-06-26T19:56:37Z
- Decision: **REJECTED**
- Data: qfa/Alpaca real daily bars via AlpacaGateway, feed `iex`, 2016-01-01 to 2026-06-25
- Controls: no CSV, no `--data-csv`, no daemon, no orders, no raw daily bars retained.

## Primary SPY result
| Cost | Sharpe | Ann. return | Ann. vol | Max DD | Activation | Ann. turnover |
|---:|---:|---:|---:|---:|---:|---:|
| 5 bps | 0.203284 | 0.013982 | 0.083989 | -0.103188 | 0.048452 | 24.419919 |
| 10 bps | 0.057949 | 0.001679 | 0.08393 | -0.157784 | 0.048452 | 24.419919 |
| 20 bps | -0.232786 | -0.022499 | 0.084009 | -0.26408 | 0.048452 | 24.419919 |

## Random/stress windows, 10 bps
Median Sharpe -0.754028; p25 -1.019815; worst -1.229227; positive-window rate 0.0 across 11 windows.

## Ablations
- Ex-ToM Sharpe: 0.057949; ToM-only Sharpe: 0.0.
- Ex-OPEX-week Sharpe: 0.533123; OPEX-week-only Sharpe: -1.373531.
- Two-day hold Sharpe: -0.128747.
- Placebo rank: 7 of 9 where 1 means best/equal among tested calendar days.

## Orthogonality
Proxy correlations: SPY buy-hold 0.456598, ToM proxy None, OPEX-week proxy 0.118625. Direct AR-006/AR-021/AR-041/AR-106 return orthogonality is marked deferred because compact artifacts do not retain those raw curves.

## Rationale
10 bps median/p25 random-window Sharpe and required calendar ablations fail acceptance gates.
