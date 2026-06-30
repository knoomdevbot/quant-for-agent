# AR-151 Evaluation

- status: rejected
- decision: source gate failed
- completed_at_utc: 2026-06-30T01:49:29Z
- performance_metrics: null
- random_window_metrics: null

Bounded source probing did not establish a parser-safe historical release/vintage table for DOL/ETA weekly initial/continuing claims values. Official DOL pages responded, but only latest/report/archive links were identified quickly; short ALFRED/FRED probes timed out. Because revised claims would risk lookahead, no ETF backtest was run and the qfa model emits zero weights.

Provenance: no_csv_used=true; no_data_csv_argument_used=true; no_daemon=true; no_orders=true; raw_daily_paths_retained=false.
