# AR-043 evaluation: ETF stress liquidity-volume dislocation detector

Suggested decision: **watchlist**.

Post-cost random-window median Sharpe 0.61968753 is positive and full-period post-cost Sharpe 0.45490526 is positive; however worst random Sharpe -0.25617409 and full-period max drawdown -0.17241563 argue for watchlist rather than acceptance.

## Data and protocol
- Data: Alpaca real daily OHLCV through qfa/AlpacaGateway only; `--data-csv` not used.
- Universe: SPY, QQQ, IWM, TLT, GLD, XLU, XLE.
- Primary qfa run: 2021-01-04 to 2025-12-15; timeframe 1Day.
- Random-period protocol: 9 staggered windows (6-12 required).
- Costs/slippage: qfa has no native cost argument; post-cost proxy subtracts 5.0 bps * one-way target-weight turnover.

## Summary metrics
| Metric | Value |
|---|---:|
| Primary post-cost Sharpe | 0.45490526 |
| Primary post-cost annualized return | 0.05663953 |
| Primary post-cost annualized volatility | 0.14444141 |
| Primary post-cost max drawdown | -0.17241563 |
| Primary post-cost total return | 0.31197395 |
| Random median post-cost Sharpe | 0.61968753 |
| Random p25 post-cost Sharpe | 0.12285326 |
| Random worst post-cost Sharpe | -0.25617409 |
| Positive random-window rate | 0.77777778 |
| Mean daily one-way turnover | 0.07359398 |
| Annualized turnover proxy | 18.54568264 |
| Estimated annual cost drag | 0.00927284 |

## Orthogonality
- Computed: True.
- Max absolute correlation: 0.63661506.
- Comparisons: AR-008_risk-off-crossasset-switch-v1=0.63661506, watchlist_tsmom-voltarget-liquid-etf-randomcost-v1=0.40480143

## Warnings
- qfa cost/slippage is post-processed, not native to the backtest engine.
- Long-only construction can retain equity beta in fast shocks.
- Do not treat this as live-trading approval; daemon and orders were not used.

## Divergent child idea
ETF stress recovery half-life allocator from volume-normalized range decay: estimate how quickly range/volume shocks decay over 2-10 sessions and allocate only when decay accelerates, rather than reacting to same-day stress breadth or inverting overnight gaps.

Artifacts: `evaluations/latest.json`, `evaluations/runs/ar043_qfa_alpaca_real_20260626T094720Z.json`.
