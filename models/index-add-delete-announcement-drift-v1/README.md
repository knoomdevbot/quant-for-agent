# index-add-delete-announcement-drift-v1

AR-141 tested whether public index addition/deletion announcements for liquid U.S. large-cap common stocks could form a timestamp-safe event source for post-announcement drift/reversal research.

## Decision

**Rejected / blocked at source gate.** The hard prerequisite was at least 150 timestamp-safe tradable events with announcement date/time or a conservative next-session lag. Public discovery did not produce such a durable corpus, so no market-bar backtest, random-window scoring, cost sensitivity, or control evaluation was run.

## Source-gate findings

- S&P 500: the reachable broad table of historical component changes is effective-date oriented and lacks per-event announcement timestamps.
- Nasdaq-100: recent annual public reconstitution press releases are timestamp-safe and name additions/deletions, but the accessible sample is sparse, below 150 events, and single-family dominated.
- Russell: the reachable LSEG reconstitution page provides current-year calendar/final broad-index files and methodology links, not a durable historical Russell 1000/large-cap announcement corpus suitable for random-window and leave-year tests.
- S&P DJI index-news pages were only partially reachable from this environment and were not a reproducible source of timestamp-safe per-security event records.

Per the issue rules, effective dates or OHLCV-inferred events were not substituted for public announcement timestamps.

## Provenance and safety

- no_csv_used: true
- no_data_csv_argument_used: true
- no_daemon: true
- no_orders: true
- raw_daily_paths_retained: false
- No raw bars, equity curves, caches, databases, credentials, or sensitive local paths are stored.

## Artifacts

- `model.py`: inactive qfa-compatible signal stub returning no signals.
- `config.yaml` and `metadata.yaml`: blocked model configuration/provenance.
- `evaluations/latest.json` and `evaluations/runs/ar141_source_gate_blocked_20260629T161151Z.json`: compact null-metric source-gate result.
- `evaluations/latest.md`: human-readable summary.
