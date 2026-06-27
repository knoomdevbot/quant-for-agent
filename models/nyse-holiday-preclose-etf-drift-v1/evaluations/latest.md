# AR-127 evaluation — NYSE holiday pre-close ETF drift

Decision: **rejected**.

Primary combined 10 bps Sharpe: `-3.19189849`; event count: `124`; hit rate: `0.44354839`.

Random-window median Sharpe: `-5.27638303`; p25: `-6.204387`; worst: `-7.67519395`; positive-window rate: `0.0`.

Placebo percentile vs random labels: `0.14`. Matched same-weekday placebo Sharpe: `-1.82465301`.

Controls: no_csv_used true; no_data_csv_argument_used true; no_daemon true; no_orders true; raw_daily_paths_retained false.

Rationale: 10 bps random-window median Sharpe not positive; 10 bps p25 random-window Sharpe materially negative; positive-window rate below 55%; random-label placebo percentile below 0.85
