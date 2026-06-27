# AR-101 evaluation — commodity inflation-shock cross-asset ETF rotation

Decision: **rejected**.

Data/provenance: qfa with Alpaca real daily OHLCV using configured paper-data access (credential values redacted). No CSV-backed data, no data CSV argument, no daemon, and no orders. Raw daily paths are not retained.

Universe: SPY, QQQ, IWM, XLE, XLB, XLI, XLF, XLV, XLP, XLU, GLD, SLV, USO, DBC, DBA, TIP, TLT, IEF, SHY, HYG, LQD

Candidate pool considered: SPY, QQQ, IWM, DIA, MDY, XLE, XLB, XLI, XLF, XLV, XLP, XLU, XLRE, GLD, SLV, USO, UNG, DBC, DBA, PDBC, GSG, TIP, TLT, IEF, SHY, HYG, JNK, LQD, BIL, UUP

Selection rationale: liquid commodity/inflation, precious-metal, duration, credit, broad equity, cyclical-sector, defensive-sector, and cash-like ETF proxies with qfa/Alpaca data availability. Exclusions were for availability/redundancy/scope rather than ex-post return selection.

Evaluation protocol: one smoke window plus nine random/stress real-data windows from 2018-01-02 through 2026-06-01 where available; daily long-only qfa `generate_signals` model; cost proxies subtract one-way turnover costs at 5/10/20 bps.

## Aggregate 10 bps cost metrics

- Windows: 10
- Median Sharpe: 0.17935255
- p25 Sharpe: -0.48002946
- Worst Sharpe: -0.49095875
- Positive Sharpe rate: 0.5
- Worst max drawdown: -0.20891193
- Mean average daily turnover: 0.09903142
- Mean activation rate: 0.52474748

## Cost sensitivity

- 5 bps median/p25/worst Sharpe: 0.29409695 / -0.3000502 / -0.37869008
- 10 bps median/p25/worst Sharpe: 0.17935255 / -0.48002946 / -0.49095875
- 20 bps median/p25/worst Sharpe: -0.07016051 / -0.79523201 / -0.8892751

## Window results at 10 bps

- smoke_2024_q1q4 (2024-01-01 to 2024-12-31): Sharpe -0.46857183, return -0.02257409, max drawdown -0.05778336, avg daily turnover 0.07879608, activation 0.404.
- stress_covid_crash_rebound (2019-07-01 to 2021-06-30): Sharpe 1.19282281, return 0.04901828, max drawdown -0.02973936, avg daily turnover 0.06581831, activation 0.36480687.
- stress_inflation_surge (2021-01-01 to 2022-12-31): Sharpe -0.48384867, return -0.09869342, max drawdown -0.20891193, avg daily turnover 0.13166886, activation 0.70318725.
- stress_2022_energy_rates (2022-01-01 to 2022-12-31): Sharpe -0.49095875, return -0.04913781, max drawdown -0.12427908, avg daily turnover 0.08425169, activation 0.404.
- stress_disinflation_ai_riskon (2023-01-01 to 2024-06-30): Sharpe 0.57976078, return 0.04898934, max drawdown -0.05742135, avg daily turnover 0.1081091, activation 0.60053619.
- random_2018_2019 (2018-01-02 to 2019-12-31): Sharpe 0.0, return 0.0, max drawdown 0.0, avg daily turnover 0.0, activation 0.0.
- random_2020_2021 (2020-04-01 to 2021-12-31): Sharpe 0.67750422, return 0.0487779, max drawdown -0.04441327, avg daily turnover 0.11027503, activation 0.5900277.
- random_2021_2023 (2021-06-01 to 2023-06-30): Sharpe -0.48566344, return -0.1052077, max drawdown -0.20891193, avg daily turnover 0.1342588, activation 0.71510516.
- random_2023_2025 (2023-06-01 to 2025-06-30): Sharpe 0.3587051, return 0.04583043, max drawdown -0.09373635, avg daily turnover 0.13256084, activation 0.71290944.
- random_2024_2026 (2024-01-01 to 2026-06-01): Sharpe 0.41293905, return 0.09363427, max drawdown -0.09460769, avg daily turnover 0.1445755, activation 0.75290216.

## Orthogonality

Deferred due to rejection. The model failed robustness/cost-sensitivity thresholds before promotion, so orthogonality against accepted/watchlist ETF alphas was not used to rescue the decision.

## Decision rationale

Rejected under the AR-101 falsifier: median 10 bps Sharpe is not enough because p25 and worst-window Sharpe are materially negative and regime concentration/cost sensitivity reduce confidence. Per issue completion rule, no refinement/direct extension child is proposed.
