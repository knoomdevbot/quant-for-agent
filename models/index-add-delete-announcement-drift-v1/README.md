# AR-141 — index-add-delete-announcement-drift-v1

**Decision:** hold — external timestamp-safe event-source dependency.

## Source-gate finding

AR-141 requires actual public index addition/deletion announcement records, used only after a conservative announcement-time lag, and blocks/rejects performance testing if fewer than 150 timestamp-safe tradable liquid common-stock events survive.

The source gate did not pass on 2026-06-29:

- Repository search found no reusable timestamp-safe S&P 500, Nasdaq-100 or Russell large-cap addition/deletion event table.
- S&P DJI `https://www.spglobal.com/spdji/en/index-announcements/` returned HTTP 403 from the research host.
- Nasdaq Trader index data page was reachable, but the checked page was general informational HTML and did not establish a historical add/delete announcement feed with timestamps.
- LSEG/FTSE Russell reconstitution page was reachable as HTML, but it did not establish a complete point-in-time historical add/delete announcement feed; a checked resource URL returned 404.
- No licensed/vendor point-in-time index announcement archive or credentials were available.

Because the core event data is unavailable/incomplete, no event study, qfa backtest, or Alpaca daily bar pull was run. Using OHLCV-inferred membership proxies, deterministic rebalance calendars, or hand-built partial announcements would violate the issue constraints.

## Required unblock condition

Provide a reproducible public or licensed source with:

- exact announcement timestamps, or conservative public-availability dates/lags;
- add/delete side, index family, effective date if available, and identifier mapping;
- common-stock/fund/preferred/warrant/OTC exclusion fields or auditable filters;
- enough historical breadth that at least 150 liquid tradable common-stock events survive after Alpaca/qfa coverage and liquidity filters.

## Safety flags

`no_csv_used:true`, `no_data_csv_argument_used:true`, `no_daemon:true`, `no_orders:true`, `raw_daily_paths_retained:false`.

## Artifacts

- Config: `models/index-add-delete-announcement-drift-v1/config.yaml`
- Metadata: `models/index-add-delete-announcement-drift-v1/metadata.yaml`
- Model stub: `models/index-add-delete-announcement-drift-v1/model.py`
- Latest JSON: `models/index-add-delete-announcement-drift-v1/evaluations/latest.json`
- Latest markdown: `models/index-add-delete-announcement-drift-v1/evaluations/latest.md`
- Run JSON: `models/index-add-delete-announcement-drift-v1/evaluations/runs/ar141_source_gate_hold_20260629T151822Z.json`
