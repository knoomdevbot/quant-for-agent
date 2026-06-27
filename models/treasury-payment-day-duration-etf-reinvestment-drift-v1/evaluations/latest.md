# AR-123 Evaluation — treasury-payment-day-duration-etf-reinvestment-drift-v1

- Decision: **rejected**
- Hypothesis: deterministic Treasury coupon/principal payment dates create same-day reinvestment support in direct Treasury duration ETFs.
- Falsifier: fail primary prior-close→payment-date-close if 5 bps median <= 0, p25 materially negative, hit rate < ~55%, placebo percentile < ~0.85, sparse/one-regime dominated, or disappears ex-ToM/month-end.
- Data: Alpaca real daily OHLCV (iex); no CSV/no `--data-csv`; no daemon; no orders; raw daily bars not retained.
- Selected primary universe: TLT, IEF, SHY, GOVT, TIP, EDV, ZROZ. Controls: LQD, HYG, BIL, SGOV.
- Calendar: ex-ante 15th and month-end Treasury payment-date proxy, business-day adjusted; excludes bill maturity amount weighting and CUSIP cash-flow sizes.

## Primary 5 bps metrics

- Event count: `142`
- Median event return: `-0.00114703`
- Mean event return: `-0.00146148`
- P25 event return: `-0.00593470`
- Hit rate: `0.4296`
- Placebo percentile (random non-event median): `0.1970`
- Annualized return / vol / Sharpe: `-0.035193` / `0.036101` / `-0.9748581455304495`
- Max drawdown: `-0.193183`; turnover proxy: `0.191117`

## Diagnostics

- 10 bps median/hit: `-0.00164703` / `0.3873`
- 20 bps median/hit: `-0.00264703` / `0.3169`
- Ex-ToM median/hit/count: `-0.0008139461800600874` / `0.4225352112676056` / `71`
- Ex-month-end median/hit/count: `-0.0021744847584336336` / `0.3829787234042553` / `94`
- Duration momentum proxy corr vs prior 5d/20d basket returns: `-0.09242904036826641` / `0.047643020778389`

## Rationale

- primary 5 bps median event return is non-positive
- primary p25 event return is materially negative
- primary hit rate below ~55%
- random non-event placebo percentile below ~0.85
- edge disappears ex-turn-of-month
- edge disappears ex-month-end

Compact JSON artifacts contain year, leave-one-year, random-window, placebo, cash/credit control, and orthogonality availability details.
