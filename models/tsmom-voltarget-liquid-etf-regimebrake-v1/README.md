# tsmom-voltarget-liquid-etf-regimebrake-v1 (AR-036)

Refinement of AR-015 ETF time-series momentum. The model holds long-only positive 126-day momentum ETF weights scaled by 20-day realized volatility, then adds an SPY stress brake and recursive smoothing / L1 turnover throttle.

## Universe
SPY, QQQ, IWM, TLT, GLD, SLV, USO, FXE, FXY. Daily bars only.

## Regime / turnover logic
- Risk-off brake sets target weights to cash when SPY 60-day drawdown is at/below -10% or SPY 20-day annualized volatility is at/above 25%.
- Risk-on weights use smoothing alpha 0.25 and max daily L1 turnover 0.50.
- qfa native costs are unavailable, so evaluation applies a 5 bps one-way ex-post turnover haircut.

## Latest evaluation
See `evaluations/latest.json` and `evaluations/latest.md`. Latest suggested decision: **rejected**.

Main 2024-2025 costed Sharpe 1.11293094, max DD -0.11454658; random-window median Sharpe 0.48820084 and p25 0.23697814 over 13 windows.

Rejected per AR-015 falsifier: costed random-window median Sharpe did not improve over AR-015, and worst random Sharpe/main drawdown worsened.
