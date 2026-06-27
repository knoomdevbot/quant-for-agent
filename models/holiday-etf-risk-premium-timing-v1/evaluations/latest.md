# AR-127 Evaluation: holiday-etf-risk-premium-timing-v1

## Protocol
- Data: Alpaca/qfa StockHistoricalDataClient daily OHLCV only; window 2018-01-01 to 2026-06-27.
- Artifacts are compact: no raw bars, daily returns, equity curves, or weight tails retained.
- Guardrails: no_csv_used=true, no_data_csv_argument_used=true, no_daemon=true, no_orders=true, raw_daily_paths_retained=false.
- Primary: equal-weight risk-on ETF basket over the pre-holiday daily interval, charged 10 bps one-way.
- Diagnostic: equal-weight defensive basket over the first post-holiday interval, charged 10 bps.
- Candidate universe: broad liquid ETFs across equity beta, sectors, credit, duration, gold/commodities/energy, and defensive/cash/FX; selection used coverage/liquidity only.

## Primary Metrics
| Test | Events | Mean | Median | P25 | Worst | Hit rate | Event Sharpe sqrt252 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Pre-holiday risk-on, 10 bps | 78 | 0.0829% | 0.0896% | -0.2278% | -2.7310% | 56.4103% | 1.89 |
| Ex-ToM/OPEX/payday/month-end | 34 | 0.2417% | 0.1242% | -0.0342% | -0.9226% | 61.7647% | 7.27 |
| Post-holiday defensive diagnostic | 78 | -0.1542% | -0.0912% | -0.3872% | -0.9868% | 38.4615% | -6.66 |

## Controls / Robustness
- Matched placebo (month + weekday, 1000 draws): observed mean rank 0.901; placebo mean median -0.0603%; placebo p95 0.1242%.
- Cost sensitivity: 5 bps median 0.1396%; 10 bps median 0.0896%; 20 bps median -0.0104%.
- ToM control median 0.0236%, hit 51.4630%; OPEX median -0.0246%, hit 47.9167%; payday median -0.0450%; month-end median 0.0235%.
- Combined pre-risk-on + post-defensive daily stream: annualized return -0.7234%, vol 2.5010%, Sharpe -0.28, max drawdown -9.5452%. This combined variant is not recommended because the post-holiday defensive leg is negative.
- Proxy correlations to combined stream: turn_of_month_risk_on_10bps=0.048, month_end_risk_on_10bps=0.020, payday_risk_on_10bps=0.070, opex_risk_on_10bps=0.115, spy_tsmom_proxy=0.089, defensive_daily=0.131.

## Decision
Suggested decision: **advance_to_refinement**.

Reason: Passes core median/hit/placebo/ex-control gates. The primary pre-holiday risk-on effect survives 10 bps and ex-calendar controls with a strong matched-placebo rank, but robustness is still sample-limited and the post-holiday defensive sleeve should be dropped or treated only as a negative diagnostic in refinement.
