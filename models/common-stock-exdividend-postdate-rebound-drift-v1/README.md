# AR-125 — Liquid common-stock ex-dividend post-date rebound/drift

Research-only qfa-compatible model for a timestamp-safe cash-dividend event study.

## Hypothesis

Liquid dividend-paying U.S. common stocks may show short-horizon rebound or drift after cash-dividend ex/process/payable mechanics because of dividend price adjustment, tax/clientele effects, reinvestment flows, and liquidity normalization.

## Falsifier

Reject if post-event returns do not survive realistic costs, have weak lower-tail/hit-rate behavior, are explained by placebo dates, SPY/beta, momentum/reversal, or dividend-yield carry, concentrate in REIT/special/fund-like names, or require unsafe announcement/as-of timestamp assumptions.

## Timestamp and data safety

- Data: Alpaca cash-dividend corporate actions plus Alpaca real daily OHLCV (IEX feed; raw price adjustment).
- Entry: first observed daily bar strictly after `max(ex_date, process_date)`.
- No pre-event exposure and no announcement timestamp assumption.
- No CSV and no `--data-csv`.
- No qfa daemon and no orders.
- No raw bars, equity curves, event tails, SQLite DBs, caches, or credentials retained.

## Evaluation summary

Period: 2024-01-01 through 2026-06-26. Primary sleeve excludes ETFs/funds/preferreds/BDCs/CEFs/ambiguous ADRs, REITs, special dividends, and foreign dividends using Alpaca asset metadata/name heuristics plus event flags.

Primary 5d / 10 bps metrics:

- Events: 2,084 across 287 symbols
- Mean event return: 0.000888614063488815
- Median event return: 0.001669066010606902
- P25 event return: -0.02237172993954087
- Positive-window rate: 0.5148752399232246
- Sharpe proxy: 0.1284697818469211
- 20 bps stress mean: -0.00011138593651118561

Decision: **rejected**. The weak hit rate, materially negative p25 return, failed 20 bps stress, and placebo comparison do not satisfy acceptance gates.

See `evaluations/latest.json` and `evaluations/latest.md` for compact metrics and diagnostics.
