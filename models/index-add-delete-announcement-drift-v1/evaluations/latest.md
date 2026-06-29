# AR-141 evaluation: index announcement source gate

**Decision:** rejected / blocked before performance evaluation.

The hard AR-141 gate required at least 150 timestamp-safe tradable liquid large-cap common-stock index addition/deletion announcement events with announcement date/time or a conservative next-session lag. Public discovery did not produce a reproducible event corpus meeting that standard.

## Compact findings

| Source | Finding | Timestamp-safe qualifying events |
| --- | --- | ---: |
| S&P 500 selected changes table | Broad historical table was reachable, but dates are effective dates, not per-event announcement timestamps. | 0 |
| Nasdaq-100 annual press releases | Recent public releases include announcement/effective dates and named adds/removes, but accessible durable sample is sparse and single-family dominated. | 42 observed, below gate |
| Russell reconstitution public page | Reachable page exposes current-year calendar/final broad Russell files, not a durable historical Russell 1000/large-cap announcement corpus. | 0 |
| S&P DJI index-news/press pages | Direct public discovery was partially inaccessible/not reproducible in this environment. | 0 |

## Metrics

No return scoring was run. All performance metrics are null because the event-source prerequisite failed before any market-bar use.

- primary Sharpe at 10 bps: null
- random-window median/p25/worst Sharpe: null
- positive-window rate: null
- 5/10/20 bps sensitivity: null
- controls/orthogonality/correlation: not evaluated

## Safety/provenance booleans

- no_csv_used: true
- no_data_csv_argument_used: true
- no_daemon: true
- no_orders: true
- raw_daily_paths_retained: false

No children were spawned because this is a rejected/blocked source-feasibility result.
