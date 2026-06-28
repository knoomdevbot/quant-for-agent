# AR-132 — U.S. share-class pair relative-value mean reversion

Research implementation for `shareclass-pair-relative-value-meanreversion-v1`.

## Hypothesis

Same-issuer listed share classes can temporarily diverge because of liquidity, voting/non-voting demand, index demand, and microstructure. A lagged log-price-ratio residual z-score should mean revert over 1–10 trading days after costs.

## Universe construction

Candidate pairs were fixed ex ante from known U.S.-listed dual/share-class structures before performance review: GOOGL/GOOG, FOXA/FOX, NWSA/NWS, BATRA/BATRK, LBRDA/LBRDK, FWONA/FWONK, LSXMA/LSXMK, LILA/LILAK, LEN/LEN.B, HEI/HEI.A, UHAL/UHAL.B, BF.A/BF.B, and BRK.A/BRK.B.

Selected by Alpaca/qfa bar coverage, overlapping history, liquidity, and economic-equivalence fit: GOOGL/GOOG, FOXA/FOX, NWSA/NWS, BATRA/BATRK, LBRDA/LBRDK, FWONA/FWONK, LILA/LILAK, LEN/LEN.B, HEI/HEI.A, UHAL/UHAL.B, BF.A/BF.B.

Exclusions: LSXMA/LSXMK due to legacy tracking-stock/listing-continuity concerns; BRK.A/BRK.B due to extreme price level and sizing/friction impracticality for this compact qfa test. Selection was not performance-based.

## Model

`model.py` exposes `generate_signals(context)` for qfa. It computes a prior-only rolling log price-ratio z-score, enters when `|z| >= 1.0`, applies a 3-day decay/holding proxy, goes long the cheap share class and short the rich share class, and gross-normalizes across active pairs.

Primary evaluation parameters: 120-day z-score, entry z 1.0, 3-day decay, 10 bps one-way cost. Sensitivity uses 5 bps one-way.

## Result

Suggested decision: **reject**.

Main failure: after 10 bps one-way turnover costs, full-sample Sharpe and random-window median Sharpe were negative, only 5% of random windows were positive, and the raw-ratio/no-zscore baseline outperformed the primary z-score model. No children spawned.

See:
- `evaluations/latest.json`
- `evaluations/latest.md`
- `evaluations/runs/ar132_qfa_alpaca_real_20260628T012217Z.json`

## Data and guardrails

Alpaca/qfa real daily OHLCV only; configured paper-data access used with credential values redacted. No CSV, no `--data-csv`, no qfa daemon, and no orders. Raw daily bars, equity curves, SQLite DBs, caches, and helper evaluator scripts are not retained in this model directory.

## Limitations

Borrow availability and short fees are not available from qfa daily bars. Exact prior-alpha daily return stream correlations were unavailable in the compact artifact workflow, so proxy correlations versus SPY/QQQ/IWM and same-universe generic mean-reversion/momentum are reported instead.
