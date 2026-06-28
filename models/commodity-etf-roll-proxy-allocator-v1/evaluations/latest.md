# AR-137 Real-Data Evaluation — commodity ETF roll-proxy allocator

Decision: **rejected**.

Data: qfa AlpacaGateway real daily OHLCV, configured paper-data access with credential values redacted. No CSV, no --data-csv, no daemon, no orders.

Universe: 18 selected from 18 candidates: USO, USL, BNO, UNG, UNL, GLD, IAU, SLV, CPER, DBB, DBA, CORN, WEAT, SOYB, DBC, PDBC, COMT, GSG. Sleeve counts: {'oil_gas': 5, 'metals': 5, 'agriculture': 4, 'broad': 4}. Excluded: {}. Analysis period: 2016-01-04 to 2026-06-26.

Protocol: weekly Friday rebalance, next-return execution via one-day lag; lagged family relative 60/120d carry proxy + 60/120d trend + lagged 60d vol sizing; 10 bps one-way turnover cost; 40 random two-year windows.

Key after-cost combined metrics:
- Full-period Sharpe: 0.4047; annualized return: 0.0557; annualized vol: 0.1688; max drawdown: -0.3804
- Random windows median Sharpe: 0.2779; p25 Sharpe: -0.0398; worst Sharpe: -0.7407; positive-window rate: 0.7000
- Mean daily turnover: 0.0638; activation: 0.9526; max avg sleeve/year weight: 0.3464

Controls random-window median Sharpe: {'carry_only': 0.2121, 'trend_only': 0.4274, 'equal_weight': 0.7382, 'tsmom': 0.4519, 'DBC_buyhold': 0.1112, 'GLD_buyhold': 0.738, 'USO_buyhold': 0.5935}.

Orthogonality: approximate control-return correlations only; max abs control correlation 0.9432. Accepted/watchlist alpha correlation deferred_due_rejection_or_fast_falsification.

Rationale: Rejected because robustness/controls/concentration thresholds were not all met.
