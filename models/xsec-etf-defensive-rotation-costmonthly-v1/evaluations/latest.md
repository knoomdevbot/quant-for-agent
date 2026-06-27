# AR-039 evaluation: xsec-etf-defensive-rotation-costmonthly-v1

Data: qfa Alpaca real market data, no CSV, symbols SPY, QQQ, IWM, XLV, XLY, XLE, XLU, XLP, TLT, IEF, GLD, 2023-01-01 to 2025-12-31. Temporary SQLite DB removed. No daemon, no trades.

## Main metrics
- Pre-cost qfa Sharpe: 0.6817; total return: 0.2687; max drawdown: -0.1679.
- Cost-adjusted Sharpe (10 bps one-way): 0.6474; total return: 0.2522; max drawdown: -0.1690.
- Annualized one-way turnover: 4.3967; mean daily one-way turnover: 0.017447.

## Random windows after costs
- Median Sharpe: 0.7386; min/max Sharpe: -0.1344/1.4126; positive windows: 5/6.
- Worst cost-adjusted max drawdown: -0.1571.

## Orthogonality
limited_parent_artifact_no_equity_curve: Mechanism is intentionally similar to AR-016 but lower-frequency/cost-aware; treat redundancy as moderate-to-high until controller can compare full retained return streams.

## Suggested decision
watchlist_continue_research: positive after-cost median random Sharpe, but not strong enough for acceptance due to weak lower-tail windows and likely parent redundancy.
