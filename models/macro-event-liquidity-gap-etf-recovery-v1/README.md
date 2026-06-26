# macro-event-liquidity-gap-etf-recovery-v1

AR-074 qfa-compatible research alpha. The model uses timestamp-safe deterministic macro-event proxies plus OHLCV gap/range stress to allocate among SPY, QQQ, IWM, TLT, GLD, XLU, XLE, and SHY.

## Signal

- Scheduled macro proxy: first Friday payroll window, CPI day-of-month window, regular FOMC-month midweek window, and mid-quarter liquidity window.
- Event confirmation: cross-ETF overnight gap z-score and intraday range z-score from Alpaca OHLCV only.
- Recovery allocation: rank stressed laggards with recent drawdown, close location, and short reversal; fallback to defensive SHY/TLT/GLD/XLU ballast outside event windows.

## Evaluation summary

Suggested decision: **rejected**

Primary 2020-2025 10 bps Sharpe: `-0.35085969`, annualized return: `-0.05621763`, max drawdown: `-0.39773669`.
Random/stress windows (12) median Sharpe: `-0.68668877`, p25 Sharpe: `-1.36313819`, worst Sharpe: `-1.97529341`, positive-window rate: `0.25`.

Controls: no CSV, no `--data-csv`, no daemon, no orders. Compact artifacts omit raw daily paths/equity curves/weight tails.

See `evaluations/latest.json` and `evaluations/latest.md` for details.
