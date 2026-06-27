# treasury-payment-day-duration-etf-reinvestment-drift-v1

AR-123 tests whether deterministic, publicly known Treasury coupon/principal payment dates create same-day reinvestment demand/support in direct Treasury duration ETFs.

## Hypothesis and falsifier

- **Hypothesis:** Treasury coupon/principal payment cash flows create same-day support in direct Treasury duration ETFs.
- **Primary leg:** hold the fixed selected Treasury-duration ETF basket from the prior close to the payment-date close only.
- **Falsifier:** reject if the primary 5 bps event return has non-positive median, materially negative p25, hit rate below ~55%, random/non-event placebo percentile below ~0.85, sparse events, one-regime dominance, or disappearance outside turn-of-month/month-end.

## Ex-ante calendar

The model uses a deterministic proxy for Treasury coupon/principal payment dates: the 15th and month-end contractual payment dates each month, adjusted to the next business day with a NYSE/Treasury-like holiday approximation. It does not infer event dates from prices and does not use CUSIP-level amount weights, bill maturity sizes, ETF flow data, or NAV premium/discount data.

## Universe

- Candidate pool: TLT, IEF, SHY, GOVT, TIP, EDV, ZROZ, LQD, HYG, BIL, SGOV.
- Primary selected universe: TLT, IEF, SHY, GOVT, TIP, EDV, ZROZ.
- Controls/cash/credit diagnostics: LQD, HYG, BIL, SGOV.

Selection was fixed before performance review using direct Treasury/duration exposure, Alpaca daily coverage, and recent liquidity sanity checks; it was not return-ranked.

## Evaluation summary

See `evaluations/latest.md` and `evaluations/latest.json` for compact real-data results. The run used Alpaca real daily OHLCV only, no CSV, no `--data-csv`, no daemon, no orders, and retained no raw daily bars/equity curves/caches.

Current suggested decision: **rejected**. Primary 5 bps event median was negative, hit rate was below threshold, placebo percentile was poor, and the effect did not survive ex-ToM/month-end diagnostics.
