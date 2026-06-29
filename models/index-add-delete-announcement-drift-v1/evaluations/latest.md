# AR-141 latest evaluation — blocked event source

Run ID: `ar141_source_gate_20260629T151851Z`

Decision: **blocked**.

The hard source gate required at least 150 timestamp-safe, reproducible public index addition/deletion announcement records in liquid U.S. large-cap common stocks before any performance evaluation. The scout found effective-date constituent-change tables for S&P 500 and Nasdaq-100 and a current Russell 1000 constituent table, but not a sufficiently broad announcement-date event archive.

## Scout summary

| Family | Public source checked | Parsed public table result | Timestamp-safe announcement records |
|---|---:|---|---:|
| S&P 500 | Wikipedia List of S&P 500 companies | ~400 historical effective-date rows | 0 |
| Nasdaq-100 | Wikipedia Nasdaq-100 | ~225 historical effective-date rows | 0 |
| Russell 1000 | Wikipedia Russell 1000 Index | current constituent table only | 0 |
| S&P Global | public index/news web page | HTTP 403 from this environment | 0 |

## Metrics

Performance metrics are unavailable by design because the source gate failed before market-data evaluation. No 1d/5d/10d/20d drift diagnostics, random windows, leave-year-out, or controls were run.

## Compliance booleans

- no_csv_used: true
- no_data_csv_argument_used: true
- no_daemon: true
- no_orders: true
- raw_daily_paths_retained: false
