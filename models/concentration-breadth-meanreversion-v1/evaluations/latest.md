# AR-116 Evaluation Result

- Decision: **rejected**
- Data: qfa/Alpaca real daily OHLCV; configured paper-data access, credentials redacted.
- Safety: no CSV, no `--data-csv`, no daemon, no orders; no raw daily bars retained.
- Selected universe: SPY, QQQ, RSP, QQQE, IWM, SHY. Candidate pool documented in JSON/config; usable full-pool coverage in this run begins 2020-08, so random windows are coverage-limited within 2020-2026.
- Primary 5 bps metrics: Sharpe `-0.504439`, annualized return `-0.016076`, vol `0.031869`, max drawdown `-0.133725`, beta to SPY `0.039662`, annualized turnover `6.25327`, activation `0.116655`.
- Random windows (30): median Sharpe `-0.653251`, p25 `-1.010749`, worst `-2.20112`, positive-window rate `0.133333`.
- Cost sensitivity: 10 bps Sharpe `-0.598917`, 20 bps Sharpe `-0.78234`.
- Orthogonality: max abs proxy correlation `0.185832`; largest rows: `[{'name': 'generic_defensive_rotation_proxy', 'correlation': -0.185832, 'n': 1483}, {'name': 'AR016_AR039_AR051_defensive_rotation_proxy', 'correlation': -0.180818, 'n': 1483}, {'name': 'AR043_stress_liquidity_proxy', 'correlation': -0.139098, 'n': 1483}, {'name': 'generic_etf_momentum_proxy', 'correlation': -0.031762, 'n': 1483}, {'name': 'AR045_AR056_megacap_reversal_proxy', 'correlation': 0.030833, 'n': 1483}]`.
- Interpretation: rejected because the concentration/breadth mean-reversion effect was not sufficiently robust after costs and proxy orthogonality/falsifier checks. No child issues created.
