# dol-eta-claims-labor-stress-etf-scout-v1

AR-151 was closed as **rejected at the source gate**.

The hypothesis required timestamp-safe weekly DOL/ETA unemployment-insurance initial/continuing claims release values, or an ALFRED/FRED vintage path, before any ETF allocation test. In bounded recovery, cheap probing found the official DOL weekly claims pages and latest-release PDF link, but did not establish a compact parser-safe historical release/vintage table. Short ALFRED/FRED probes timed out, so no reliable release/vintage evaluator was completed.

Because revised claims data would create lookahead, the model is a zero-weight qfa-compatible artifact. No ETF performance backtest was run.

## Provenance

- no_csv_used: true
- no_data_csv_argument_used: true
- no_daemon: true
- no_orders: true
- raw_daily_paths_retained: false

## Decision

Rejected, not on performance, but because the required timestamp/vintage source gate was not satisfied inside the bounded recovery window.
