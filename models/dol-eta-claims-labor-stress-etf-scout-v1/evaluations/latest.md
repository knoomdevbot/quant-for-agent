# AR-151 source-gate run

- Run ID: `ar151_source_gate_20260630T005946Z`
- Decision: **source gate passed in principle; performance not evaluated**
- Model: `dol-eta-claims-labor-stress-etf-scout-v1`

## Rationale

Official DOL/ETA pages provide a timestamp-safe path in principle: the DOL weekly claims archive points to dated DOL newsroom ETA release pages for "Unemployment Insurance Weekly Claims Report". Those dated releases can be snapshotted/parsed as point-in-time weekly values and traded only after public release. ALFRED also documents an archival initial-claims series, but the programmatic vintage API route was not used here because it requires an external credential.

## Evaluation status

No performance backtest was run in this bounded recovery pass. Metrics are unavailable/null. The model wrapper is disabled and returns zero weights.

## Safety flags

- no_csv_used: true
- no_data_csv_argument_used: true
- no_daemon: true
- no_orders: true
- raw_daily_paths_retained: false
