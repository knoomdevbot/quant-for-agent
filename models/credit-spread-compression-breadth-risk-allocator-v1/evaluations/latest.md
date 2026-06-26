# AR-102 evaluation — credit-spread compression breadth risk allocator

## Decision

Suggested decision: **rejected**.

Fails falsifier after realistic cost proxy: random/stress median Sharpe is not positive enough, p25 is negative, and 10/20 bps turnover costs make the distribution materially worse.

## Data and protocol

- Data: qfa Alpaca real daily OHLCV via configured paper-data access; credentials redacted.
- Controls: no CSV, no data-csv argument, no daemon, no orders.
- Universe: HYG, JNK, LQD, VCIT, TIP, TLT, IEF, SHY, SPY, QQQ, IWM, XLF, XLI, XLE, XLU, XLP, XLV, GLD.
- Candidate pool considered: HYG, JNK, SJNK, LQD, VCIT, VCSH, AGG, BND, TIP, TLT, IEF, SHY, SPY, QQQ, IWM, DIA, XLF, XLI, XLE, XLU, XLP, XLV, XLRE, GLD, SLV, UUP.
- Windows: smoke + primary full-period + 11 random/stress windows.
- Cost proxy: one-way daily turnover cost at 5, 10, and 20 bps.
- Raw daily curves/weights are not retained; artifacts are compact summaries only.

## Primary full-period result

- Window: 2019-01-01 to 2026-06-20.
- Pre-cost qfa Sharpe: 0.07141004; total return: 0.01509569; max drawdown: -0.18728073.
- 5 bps Sharpe: -0.39685573; total return: -0.16920317; max drawdown: -0.22712564.
- 10 bps Sharpe: -0.86131868; total return: -0.32013159; max drawdown: -0.33916479.
- 20 bps Sharpe: -1.76098477; total return: -0.54489551; max drawdown: -0.54690397.
- Avg daily turnover: 0.27050704; annualized turnover: 68.167775; activation rate: 0.8993923.

## Random/stress Sharpe distribution

- 5 bps: median 0.0; p25 -0.25450581; worst -1.13943037; positive-rate 0.45454545.
- 10 bps: median -0.31450657; p25 -0.5593595; worst -1.36494874; positive-rate 0.09090909.
- 20 bps: median -1.05350545; p25 -1.21123264; worst -1.80429055; positive-rate 0.0.

## Watchlist / rejected

- Status: rejected.
- No child refinement is suggested when rejected, per AR-102 completion rule.
