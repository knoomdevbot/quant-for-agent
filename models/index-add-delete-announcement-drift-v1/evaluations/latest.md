# AR-141 latest evaluation

**Decision:** hold — external timestamp-safe index announcement event-source dependency.

## Metrics

No return backtest was run because the mandatory source gate failed.

- Required timestamp-safe tradable events: 150
- Accepted timestamp-safe tradable events: 0
- Primary after-cost Sharpe at 10 bps one-way: null
- Random-window median Sharpe: null
- Random-window p25 Sharpe: null
- Random-window positive rate: null
- 20 bps sensitivity: null
- Max correlation / orthogonality: null

## Source-gate evidence

- Clean worktree/repository search found no reusable timestamp-safe historical S&P 500, Nasdaq-100 or Russell large-cap addition/deletion event table.
- S&P DJI index announcements URL returned HTTP 403 from the research host.
- Nasdaq Trader index-data page returned HTTP 200 HTML, but the checked page did not establish a complete historical timestamp-safe Nasdaq-100 addition/deletion announcement feed.
- LSEG/FTSE Russell reconstitution URL returned HTTP 200 HTML, while a checked resources URL returned 404; no complete PIT add/delete feed was established.
- No licensed/vendor point-in-time index announcement source or credentials were available.

## Blocking reason

AR-141 depends on actual public announcement records with timestamp-safe availability. Without that source, any qfa/Alpaca performance run would have to use inferred calendar, rebalance, or OHLCV/membership proxies, which the issue explicitly forbids. This is therefore a **hold**, not a null performance rejection.

## Controls and orthogonality

Deferred due hold. Matched non-events, generic momentum/reversal, calendar controls, shifted announcement-date placebo, concentration diagnostics, and alpha-library correlation require an accepted event set and return stream.

## Safety flags

`no_csv_used:true`, `no_data_csv_argument_used:true`, `no_daemon:true`, `no_orders:true`, `raw_daily_paths_retained:false`.

## Unblock condition

Provide a reproducible public or licensed point-in-time event source with announcement timestamps or conservative availability dates, add/delete side, index family, identifier mapping, fund/preferred/warrant/OTC/common-stock filters, and enough historical breadth for >=150 liquid tradable Alpaca/qfa-covered common-stock events after filters.
