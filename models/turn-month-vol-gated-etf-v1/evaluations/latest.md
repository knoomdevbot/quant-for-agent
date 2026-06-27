# AR-041 evaluation: turn-month-vol-gated-etf-v1

Suggested decision: **reject_falsified_by_lower_tail_or_parent_comparison**.

Costed random median Sharpe -0.12131964, p25 -0.5080568, worst -2.25284534 versus parent median 1.09846694, p25 0.14313315; worst drawdown -0.09633951 versus parent -0.22133662.

## Primary cost-adjusted metrics
- Sharpe: 0.57767932
- Annualized return: 0.04663994
- Annualized volatility: 0.08520483
- Max drawdown: -0.18566424
- Total return: 0.2544016
- Turnover: total one-way 24.5, annualized 4.9273743

## Random-period protocol
8 deterministic windows, qfa Alpaca real data only, no `--data-csv`, 5 bps one-way ex-post turnover haircut.

- Median Sharpe: -0.12131964
- P25 Sharpe: -0.5080568
- Worst Sharpe: -2.25284534
- Positive window rate: 0.375
- Worst max drawdown: -0.09633951
- Parent AR-021 same-window median/p25/worst Sharpe: 1.09846694 / 0.14313315 / -1.19719169
- Parent AR-021 same-window worst drawdown: -0.22133662

## Orthogonality
Parent AR-021 cost-adjusted daily return correlation: 0.63722267 over 1252 overlapping periods. Additional retained latest.json equity-curve correlations are in `latest.json`.

## Warnings
- qfa backtester normalizes any nonzero weights to 1.0 gross, so exposure reduction is implemented as active/flat gating only.
- AR-021 parent observed-session end-of-month logic uses only sessions available as of context; this can make the pre-month-end leg broad in qfa replay, so results should be interpreted as refinement of the implemented AR-021 artifact rather than a pure future-known last-session calendar.
- qfa has no native transaction-cost/slippage support; 5 bps one-way turnover haircut is ex-post.
- No daemon was run, no orders/trades were placed, no secrets are stored in artifacts.
