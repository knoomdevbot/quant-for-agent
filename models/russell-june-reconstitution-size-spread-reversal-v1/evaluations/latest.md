# AR-126 Evaluation — russell-june-reconstitution-size-spread-reversal-v1

- **Decision:** rejected
- **Data:** qfa/Alpaca real daily OHLCV; configured paper-data access with values redacted.
- **Controls:** no CSV, no data-csv argument, no daemon, no orders; compact summaries only.
- **Universe:** IJR, IWB, IWD, IWF, IWM, IWN, IWO, MDY, VBK, VBR, VTI, VTWO from candidate pool IWM, IWB, VTWO, VTI, IJR, MDY, RSP, IWF, IWD, IWO, IWN, VTV, VB, VBR, VBK.
- **Primary rule:** reverse 5-trading-day pre-event size/style spread pressure, enter next trading day after last Friday in June, hold 5 trading days.

## Primary 10 bps metrics

- Usable events: 9 (2017-2025)
- Mean event return: 0.00052177
- Median event return: -0.00108209
- P25 / worst: -0.00218099 / -0.00601856
- Positive-event rate: 0.44444444
- Daily Sharpe during event holds: 4.06271992
- Max drawdown during event holds: -0.00801675
- Avg gross turnover/event: 2.0

## Cost sensitivity

- 5 bps mean/median: 0.00152177 / -8.209e-05
- 10 bps mean/median: 0.00052177 / -0.00108209
- 20 bps mean/median: -0.00147823 / -0.00308209

## Baseline checks

- June fixed long IWM / short IWB mean: -0.00437852
- June fixed short IWM / long IWB mean: 0.00035793
- June pressure momentum mean: -0.00451999
- June ETF TSMOM 63d mean: 0.01212943
- Non-June placebo mean-of-monthly-means: -0.00141364; months beating primary mean: 3

## Rationale
- fewer than 12 usable annual June events
- primary 10 bps median event return is not positive
- positive-year rate does not clear >50% gate
- does not beat ETF TSMOM-style June baseline

Orthogonality to accepted/watchlist library: unavailable/deferred_due_rejection.
