# Single-name post-OPEX range-release residual continuation v1 (AR-126)

Research-only qfa alpha model for the hypothesis that liquid large-cap single names compressed into standard monthly OPEX continue in the direction of their first post-OPEX sector-residual move. The model exposes `generate_signals(context)` and uses only completed qfa/Alpaca daily OHLCV plus a deterministic third-Friday OPEX calendar. It does not use CSV input, `--data-csv`, daemon execution, or orders.

## Implementation

- Universe: 120 fixed liquid large-cap/common-stock candidates selected by Alpaca coverage and median dollar volume; sector ETF controls are XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV, XLY, with SPY/QQQ diagnostics.
- Feature gate: 5-day pre-OPEX daily range compression vs trailing 60-day median and muted sector-residual movement vs trailing 60-day median.
- Confirmation: first trading day after standard monthly OPEX; direction is the first post-OPEX close-to-close sector-residual move.
- Portfolio: equal-risk-like score, gross-normalized, capped by name and sector; 5-day research hold in evaluation.

## Latest real-data result

Decision: **rejected** — Primary after-cost median random-window Sharpe is not positive enough and hard placebo/reversal ablations are not convincingly beaten.

Primary after-cost (5 bps one-way): Sharpe -0.3944, annualized return -0.0054, annualized vol 0.0134, max drawdown -0.0484, events 11, hit rate 0.2727272727272727.

Random-window protocol: 30 sampled 1-year windows; median Sharpe -0.5647, p25 Sharpe -0.5732, worst Sharpe -1.3489, positive-window rate 0.1333.

Hard ablations did not support the hypothesis: matched non-OPEX Sharpe 0.0755, shifted-Friday Sharpe 0.1984, generic range Sharpe -0.0346, raw no-residual Sharpe 0.1385, reversed-direction Sharpe 0.2683.

## Provenance and limitations

Artifacts were generated from Alpaca real daily OHLCV through the qfa gateway with paper-data credentials loaded transiently and redacted from committed files. No raw bars, equity curves, caches, SQLite DBs, CSVs, or weight tails are retained. Missing/limited diagnostics are marked in `evaluations/latest.json`, including earnings contamination exclusion and related-model return-stream correlations.
