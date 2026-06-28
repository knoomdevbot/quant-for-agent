# AR-135 evaluation: CFTC COT positioning extreme-unwind ETF allocator

- Created: 2026-06-28T03:57:56Z
- Data: qfa AlpacaGateway real ETF daily bars; official CFTC public historical files parsed in memory; no CSV price data; no `--data-csv`; no daemon; no orders.
- Selected universe: GLD, SLV, USO, UNG, TLT, IEF, UUP, SPY, QQQ, IWM
- Candidate pool: 19 issue ETFs; selected by Alpaca coverage, liquidity proxy, and clean CFTC futures mapping.
- Release lag: Tuesday COT report + Friday public release, traded next business day.

## Hypothesis / falsifier
Weekly CFTC positioning extremes plus 4-week changes should flag crowded futures exposures that unwind in ETF proxies over 5-20 trading days. Falsified if costed random windows fail median/lower-tail gates or if position-only/price-only/placebo controls explain the result.

## Metrics (10 bps primary cost)

| metric | value |
|---|---:|
| Primary Sharpe | -0.1699 |
| Primary max drawdown | -0.1551 |
| Primary annualized turnover | 8.3221 |
| Primary activation rate | 0.5709 |
| Random median Sharpe | 0.0000 |
| Random p25 Sharpe | -0.5940 |
| Random worst Sharpe | -1.7069 |
| Random positive-window rate | 0.4667 |
| Random worst max drawdown | -0.1551 |

## Controls

| control | Sharpe | max DD | ann. turnover | activation |
|---|---:|---:|---:|---:|
| position_only | 0.1264 | -0.1304 | 4.8994 | 0.6759 |
| price_only | 0.1167 | -0.3928 | 39.1003 | 0.9824 |
| shifted_release | -0.5733 | -0.2157 | 8.2505 | 0.5693 |
| lagged_release | -0.2026 | -0.1494 | 7.7051 | 0.5778 |
| same_weekday_placebo | 0.2908 | -0.1585 | 18.4377 | 0.6034 |

## Orthogonality

- Attempted: True
- Max available absolute correlation: 0.1060069
- Note: See latest.json for top compact-artifact comparisons.

## Decision

**REJECTED**. Gate pass: False. Lower-tail and control/placebo robustness determine status; see JSON for full random-window run list and mapping diagnostics.
