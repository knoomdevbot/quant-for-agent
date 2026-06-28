# AR-139 latest evaluation

**Decision:** blocked / rejected.

## Metrics

No return backtest was run because the point-in-time prerequisite failed.

- Selected universe count: 0
- Accepted timestamp-safe filing observations: 0
- SEC company_tickers rows: 10,433
- Rough common-like candidates after simple name/ticker exclusions: 9,213
- Sampled liquid common tickers with companyfacts fetched: 40
- Current-endpoint sample fact entries across intended tags: 50,029, **not accepted as PIT-safe**
- Median random-window Sharpe: null
- P25 random-window Sharpe: null
- Worst random-window Sharpe: null
- Positive-window rate: null
- Max drawdown: null
- Turnover: null
- 20 bps sensitivity: null
- Max correlation / orthogonality: null

## Blocking reason

SEC companyfacts is available as a current compiled endpoint. Although facts include `filed` dates, the run observed multiple filed/accession entries for the same historical tag/unit/fiscal-period/end-date keys, consistent with amendments/restatements/reclassifications. Without a true as-filed archive or historical point-in-time fundamental store, ranking old post-filing signals from today's companyfacts would risk hindsight.

## Controls and orthogonality

Not evaluated. AR-010 quality proxy, price momentum/low-vol/value/size/liquidity buckets, randomized or shifted filing-date placebo, no-filing calendar baseline, and single-feature variants require an accepted alpha return stream, which was not produced.

## Safety flags

`no_csv_used:true`, `no_data_csv_argument_used:true`, `no_daemon:true`, `no_orders:true`, `raw_daily_paths_retained:false`.
