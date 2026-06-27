# AR-124 — Post-split effective-date liquidity/attention drift

Decision: **rejected**.

This qfa-compatible research model tests whether liquid U.S. equities drift after forward stock split effective/ex/process dates. The design is timestamp-safe by construction: positions are opened only after the split event date, with no assumption that announcement timestamps are available before the event.

## Data and controls

- Data source: Alpaca corporate-action split records plus Alpaca real daily OHLCV.
- No CSV, no `--data-csv`, no daemon, and no orders.
- Raw daily bars, equity curves, and weight tails were not retained.
- Primary sleeve: liquid forward splits only; reverse/unit splits are diagnostics.

## Universe

Candidate pool: 74 forward-split symbols / 79 forward split records from 2020-01-01 through 2026-06-26 before final liquidity/event filters.

Selected symbols: AAON, AIV, AMZN, ANET, APG, APH, AVGO, BEPC, BKNG, BN, CELH, CHDN.

Key limitations: only 14 primary liquid forward-split events survived filters; results are therefore sparse and sensitive to event/year concentration.

## Primary result

Primary 5-day / 10 bps sleeve:

- event_count: 14
- median Sharpe proxy: 0.2405
- p25 Sharpe proxy: 0.1226
- worst year Sharpe proxy: -0.4900
- mean event return: 1.16%
- median event return: 0.29%
- p25 event return: -1.82%
- hit / positive-window rate: 50%
- max drawdown proxy: -18.83%
- turnover proxy: 1.88%

The candidate was rejected because the primary hit rate failed the 55% gate, p25 event return was materially negative, event count was too sparse, and beta proxy correlation to SPY same windows was high (~0.70). No direct children should be spawned from this rejected hypothesis.
