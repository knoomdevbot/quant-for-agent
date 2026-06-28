# sec-form4-insider-purchase-cluster-drift-v1

AR-134 recovery artifact for the hypothesis that clustered open-market insider purchases disclosed on SEC Form 4 may produce 5--20 trading-day post-filing drift.

## Decision

**Blocked/rejected.** The prior full evaluation timed out, and this bounded recovery run did not complete construction of a timestamp-safe SEC Form 4 point-in-time event table. No event performance metrics are available, and no Sharpe or return statistics are reported.

## What was attempted

- Confirmed quick public SEC reachability with a small `company_tickers.json` head fetch.
- Did **not** attempt a large SEC scrape.
- Did **not** run qfa daemon.
- Did **not** place orders.
- Did **not** use CSV-backed market data or `--data-csv`.
- Did **not** retain raw filing or daily-bar paths.

## Missing prerequisite

A valid evaluation requires a PIT event table with SEC Form 4 acceptance timestamps, XML non-derivative transaction parsing, transaction code `P`, acquisition flag `A`, officer/director role identification, distinct-insider clustering, CIK/ticker mapping, liquidity filters, and qfa/Alpaca daily OHLCV coverage. That table was not completed in this bounded recovery run.

## Model behavior

`model.py` exposes `generate_signals(context)` but intentionally returns `{}`. This prevents fabricated signals or trading on incomplete event data.

## Metrics

All performance metrics are unavailable/null due to event-source construction failure.
