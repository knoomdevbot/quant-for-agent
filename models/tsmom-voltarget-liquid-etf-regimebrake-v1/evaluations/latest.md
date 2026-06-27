# AR-036 Evaluation — tsmom-voltarget-liquid-etf-regimebrake-v1

- Created UTC: 2026-06-26T08:56:54Z
- Data: Alpaca real market data via qfa/AlpacaGateway only; no CSV; symbols SPY, QQQ, IWM, TLT, GLD, SLV, USO, FXE, FXY.
- qfa smoke/main run: ok; temp DB run id 1 (DB deleted: True).
- Main 2024-01-01..2025-12-31 5 bps costed Sharpe: 1.11293094; return 0.31053394; max DD -0.11454658.
- Main turnover: avg daily 0.02983999; annualized proxy 7.51967845.
- Random windows (13): median Sharpe 0.48820084; p25 0.23697814; worst -0.7165961; positive 12/13; worst max DD -0.25127716.
- Parent AR-015 reference: {'main_5bps_sharpe': 1.13279897, 'main_max_drawdown_5bps': -0.09458803, 'random_median_5bps_sharpe': 0.52258623, 'random_p25_5bps_sharpe': 0.11562103, 'random_worst_5bps_sharpe': -0.51612569, 'random_positive_rate_5bps': 0.84615385, 'random_worst_costed_max_drawdown': -0.29365532}.
- Suggested decision: **rejected** — missed AR-015 falsifier: median and worst random-window Sharpe did not improve over AR-015; main Sharpe/DD also worse, despite lower turnover.

## Orthogonality (costed daily return correlation, top available)
- tsmom-voltarget-liquid-etf-randomcost-v1: corr 0.939443 over 499 days
- meanrev-zscore-liquid-etf-1d-v1: corr 0.125013 over 499 days

## Child suggestion policy
- No refinement/extension/direct inversion suggested because this result is rejected.
- One genuinely divergent child only: ETF carry/term-structure defensive allocation using carry/real-rate drivers rather than price momentum regime brakes.
