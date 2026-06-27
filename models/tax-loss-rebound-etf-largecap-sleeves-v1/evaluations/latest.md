# AR-123 Real-Data Evaluation: tax-loss-rebound-etf-largecap-sleeves-v1

Decision: **rejected**.

## Protocol
- Data: qfa AlpacaGateway real daily OHLCV, 2015-12-01 through 2026-01-15; no CSV, no data-csv argument, no daemon, no orders.
- Universe fixed before ranking: ETF candidates 41 -> selected 24; equity candidates 50 -> selected 30 by historical coverage/liquidity only.
- Primary signal: last trading day on/before Dec 20; entry at last December close; hold first five January trading days.
- Cost: 10 bps one-way turnover primary, with 5/20 bps sensitivity.

## Selected universe
- ETF sleeve: SPY, QQQ, IWM, HYG, EEM, TLT, LQD, XLF, EFA, GLD, XLE, DIA, XLV, XLK, XLI, XLU, SMH, XLP, XLY, VTI, IYR, XBI, XOP, IEF
- Equity sleeve: TSLA, AAPL, AMZN, MSFT, NVDA, META, GOOGL, GOOG, BAC, JPM, V, XOM, BA, INTC, UNH, BRK.B, JNJ, DIS, HD, CVX, MA, PFE, QCOM, CSCO, PG, T, WMT, COST, VZ, GE

## Primary 5-day January net results at 10 bps one-way
| Sleeve | Events | Mean | Median | P25 | Worst | Event Sharpe | Positive-year rate | Worst hold DD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| etf | 9 | 1.46% | 0.95% | 0.16% | -3.18% | 0.543169773843455 | 77.78% | -2.98% |
| equity | 9 | 2.50% | 2.23% | 1.63% | -0.98% | 1.2640646988825994 | 88.89% | -2.07% |
| combined | 9 | 1.98% | 1.29% | 0.88% | -0.69% | 0.9140793044997478 | 77.78% | -1.78% |

## Baselines (5-day January net, 10 bps one-way)
| Baseline | Mean | Median | P25 | Worst | Positive-year rate |
|---|---:|---:|---:|---:|---:|
| jan_no_loser_equal_selected | 1.24% | 1.37% | 0.40% | -0.44% | 77.78% |
| spy | 0.83% | 1.14% | 0.38% | -2.07% | 77.78% |
| simple_tom_early_jan_equal_selected | 1.24% | 1.37% | 0.40% | -0.44% | 77.78% |
| short_lookback_reversal | 1.60% | 1.17% | 0.90% | -2.47% | 88.89% |
| tsmom_positive_ytd_or_cashproxy | 0.64% | 0.87% | -0.55% | -1.44% | 66.67% |

## Decision rationale
Failed gates: beats_jan_no_loser_median, with orthogonality unavailable rather than passing. The strict decision is **rejected** because the combined basket does not clear baseline/sleeve robustness gates under the sparse annual-event protocol.

Orthogonality: max_corr_to_library unavailable; available watchlist artifacts did not retain aligned annual event-return streams for this Dec/Jan event horizon.

Child policy: No child ideas spawned because decision is rejected.
