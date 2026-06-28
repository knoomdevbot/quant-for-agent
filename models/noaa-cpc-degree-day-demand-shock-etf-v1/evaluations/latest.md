# AR-136 evaluation — NOAA/CPC degree-day demand-shock ETF allocator

Decision: **rejected**.

Primary 10 bps metrics: Sharpe -1.025, annualized return -8.500%, max drawdown -17.393%, annualized turnover 12.19, activation 25.3%, active events 23.

Random-window metrics (80 x 63 sessions): median Sharpe -0.558, p25 -2.321, worst -4.233, positive-window rate 33.8%.

Event-window diagnostics: median 5-session event return 0.402%, positive event rate 52.2%, worst event return -2.938%.

Controls: same-weekday placebo Sharpe -0.148; shifted-release labels 0.363; inverted weather 0.740; seasonality/month-only -0.066; energy 63d TSMOM -0.124; energy reversal 0.124.

Data: official NOAA/CPC archived weekly degree-day state files parsed in memory with visible archive modified timestamps; real ETF daily bars from qfa AlpacaGateway configured paper-data access. No CSV price data, no --data-csv, no daemon, no orders.

Limitations: older archive files have bulk 2025 modified timestamps and were excluded for timely evaluation, so the timestamp-safe sample is short; archive timezone is unstated and handled with conservative next-calendar-day session lag; EIA/storage was not directly ingested.
