# AR-118 Evaluation Result

- Status suggestion: **rejected**
- Data: qfa/Alpaca real daily OHLCV; no CSV, no `--data-csv`, no daemon, no orders.
- Primary 10 bps full-period Sharpe: `-1.241678`; annualized return: `-0.175841`; max drawdown: `-0.674394`; turnover: `0.617948`.
- Random windows: median Sharpe `-1.7066`, p25 `-2.1835`, worst `-2.9676`, positive-window rate `0.0` over `30` windows.
- Max abs correlation to ETF/proxy benchmarks: `0.4464`.

## Decision rationale
- Failed acceptance thresholds: primary/random-window 10 bps Sharpe and positive-window breadth are not compelling.

## Key warnings
- Alpaca/IEX paper-data access may provide truncated historical coverage before 2020 for many ETFs; metrics use returned real bars only.
- Daily close-to-next-close replay is an approximation and not an intraday execution simulator.
- Proxy orthogonality cannot fully test AR-015/037/049/051/060/061/067/071/105 without retained raw return streams.

## Artifacts
- Latest JSON: `models/defensive-carry-pullback-recovery-allocator-v1/evaluations/latest.json`
- Immutable run JSON: `models/defensive-carry-pullback-recovery-allocator-v1/evaluations/runs/ar118_qfa_alpaca_real_20260627T043642Z.json`
