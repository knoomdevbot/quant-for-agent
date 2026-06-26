# AR-055 evaluation: ETF stress recovery half-life allocator

- Decision: **reject**
- Data: Alpaca real daily OHLCV via qfa; `--data-csv` not used.
- Primary window: 2021-01-04 to 2025-12-15; qfa run id 1 (temporary DB removed).
- Primary post-cost Sharpe: 0.27749142; annual return: 0.0303924; vol: 0.14891902; max DD: -0.17356821.
- Random windows: 9; median post-cost Sharpe: 0.654380; p25: -0.121457; positive-window rate: 66.67%.
- Cost proxy: 5 bps * one-way daily target turnover; mean daily turnover 0.18346247.
- Orthogonality max abs correlation: 0.98065061; details in latest.json.

## Rationale
Rejected: median random-window post-cost Sharpe 0.6544, p25 -0.1215, max abs orthogonality corr 0.98065061.

## Notes
No daemon, no orders. Temporary SQLite DBs removed after JSON capture.
