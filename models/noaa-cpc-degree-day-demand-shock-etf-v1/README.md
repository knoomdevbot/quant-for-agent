# NOAA/CPC degree-day demand-shock ETF allocator (AR-136)

Decision: **rejected** after timestamp-safe real-data evaluation.

## Summary

This research tested whether public NOAA/CPC weekly heating/cooling degree-day deviations, used only after visible CPC archive modified timestamps, could allocate a weather-sensitive ETF sleeve (`UNG`, `USO`, `XLE`, `XOP`, `XLU`, `ICLN`, `TAN`). ETF bars came from qfa/Alpaca configured paper-data access. No CSV price data, no `--data-csv`, no daemon, and no orders were used.

The model implements the fixed rule for qfa contexts that supply timestamp-safe `degree_day_features` or `degree_day_signal_history`. It does not fetch NOAA/CPC data at runtime.

## Result

Primary 10 bps Sharpe was -1.025 with -17.39% max drawdown. Random-window median Sharpe was -0.558, p25 -2.321, worst -4.233, and positive-window rate 33.75%. Shifted/inverted controls were not supportive, so the alpha was rejected.

See `evaluations/latest.json` and `evaluations/latest.md` for compact metrics, source/timestamp notes, controls, and limitations.
