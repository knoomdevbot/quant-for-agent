# Country ETF stale-participation catch-up v1 (AR-117)

Research-only qfa model for US-listed country/region ETFs. It ranks country ETFs by a price-only stale-participation residual versus lagged global-risk moves, recent range, and dollar-volume participation, then takes a constrained long/short basket for next-session evaluation.

Data/evaluation constraints satisfied: qfa/Alpaca real daily OHLCV only; no CSV; no `--data-csv`; no daemon; no orders; no raw daily data/equity curves/weights tails retained.

Selected universe (10): EEM, FXI, EWZ, KWEB, EWJ, MCHI, INDA, EWY, VGK, EWT. Candidate pool and filter table are in `evaluations/latest.json`.

Latest decision: **rejected**. Primary 5 bps random-window median Sharpe -0.901032, p25 -1.442698, worst -1.956451, positive-window rate 0.066667.

See `evaluations/latest.md` and immutable run `models/country-etf-stale-participation-catchup-v1/evaluations/runs/ar117_qfa_alpaca_real_20260627T025416Z.json` for compact results and falsifier controls.
