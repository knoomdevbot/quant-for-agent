# AR-057 evaluation: range-compression-breakout-megacap-v1

Created: 2026-06-26T11:11:05Z

## Result

Suggested decision: **reject**.

Primary 2024-2025 pre-cost qfa Sharpe: -0.34131536; total return: -0.14827321; max drawdown: -0.35605955.
Primary cost-adjusted Sharpe after 5 bps turnover haircut: -0.39119607; total return: -0.16382098; max drawdown: -0.36234972.

Random windows: 8; median cost-adjusted Sharpe: 0.27437433; positive Sharpe fraction: 0.625.

## Orthogonality

- AR-045 closing-volume-reversal-costaware-megacap-v1: corr=-0.089996 overlap=500 
- AR-028 closing-volume-reversal-megacap-v1: corr=-0.433346 overlap=500 
- mega-cap equal-weight proxy: corr=-0.192483 overlap=500 
- SPY market proxy: corr=-0.263962 overlap=500 
- tsmom-voltarget-liquid-etf-randomcost-v1 watchlist: corr=-0.056282 overlap=499 

## Data and execution notes

Used qfa CLI with Alpaca real daily market data only, credentials from profile secret environment (values not printed), no CSV/`--data-csv`, no daemon, no orders. Temporary SQLite DB paths were removed after retaining immutable JSON run artifacts under `evaluations/runs/`.

Run summary artifact: `/Users/moonk/quant-for-agent/models/range-compression-breakout-megacap-v1/evaluations/runs/ar057_qfa_alpaca_real_20260626T111105Z.json`

## Bad-result policy

Rejected: do not spawn direct AR-057 refinements. At most one genuinely divergent follow-up is suggested: **ETF index gap-follow-through after overnight futures shock**, which tests index-level overnight information assimilation rather than extending mega-cap range-compression breakouts.
