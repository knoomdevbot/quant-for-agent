# AR-123 evaluation summary

- Data: qfa/Alpaca real daily OHLCV, daily bars. No CSV, no data-csv argument, no daemon, no orders.
- Usable annual events: 9.
- Combined 10 bps median return: 0.00365759; p25: -0.00626644; worst: -0.017882; daily-event Sharpe: 4.62613502; max event hold drawdown: -0.02147554; hit rate: 0.55555556; one-way turnover: 1.0.
- ETF sleeve median return: -0.00142667; p25: -0.00662689; worst: -0.0333529.
- Large-cap equity sleeve median return: 0.01202524; p25: -0.00593997; worst: -0.02067395.
- Baseline gate: generic January/no-loser equal-selected median return 0.01447805; SPY-only median 0.0149458; short-lookback mean-reversion median 0.01138546.
- Orthogonality: deferred_due_rejection; compact library streams were not available in an aligned annual-event form and rejection was determined by the baseline gate.
- Decision: **rejected** — Rejected: primary combined loser basket is positive but does not beat the generic January/no-loser equal-selected baseline at 10 bps; evidence is sparse and baseline-sensitive.

Failure modes: sparse annual sample, possible large-cap survivorship bias, ETF tax-loss mechanism weaker than single names, and sensitivity to generic January risk exposure.
