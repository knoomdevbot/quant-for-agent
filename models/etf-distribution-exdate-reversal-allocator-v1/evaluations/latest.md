# AR-120 — ETF distribution ex-date reversal allocator

**Status recommendation:** rejected / blocked by timestamp-safety gate (do not add to watchlist).

## What was checked

- Used real Alpaca-compatible access for the predeclared candidate ETF pool: HYG, LQD, SHY, IEF, TLT, GOVT, TIP, EMB, MUB, VCIT, VCSH, BND, AGG, XLU, XLP, XLV, VNQ, XLRE.
- Queried Alpaca daily bars and Alpaca cash-dividend corporate-action records for 2018-01-01 through 2025-12-31.
- Did not use CSV input or `--data-csv`; did not run qfa daemon; did not place orders; did not retain raw bars, event rows, DBs, caches, or helper scripts.

## Coverage findings

- Alpaca cash-dividend endpoint was reachable and returned 1,399 cash-dividend records across the pool.
- All 18 symbols had daily bar coverage in the query result and passed the pre-performance coverage/liquidity screen.
- Observed corporate-action fields: corporate_action_type, cusip, due_bill_off_date, due_bill_on_date, ex_date, foreign, id, payable_date, process_date, rate, record_date, special, symbol.

## Blocking issue

The issue requires timestamp-safe event knowledge before a trading decision. The observed Alpaca cash-dividend records include ex-date, payable date, record date, process date, and rate, but **do not include an announcement/as-of/knowledge timestamp**. Therefore historical decision-time availability cannot be verified without look-ahead risk.

Per AR-120 constraints, I did not infer ex-dates from OHLCV price drops and did not run performance tests on non timestamp-safe events. The durable `model.py` is a safe cash/zero-weight stub.

## Metrics

No performance metrics were generated because the alpha was blocked before backtesting.

- 5/10/20 bps cost sensitivity: not evaluated
- random-period Sharpe / p25 / positive-window rate: not evaluated
- event-year/window stratification: not evaluated
- orthogonality vs existing alphas: not evaluated

## Failure modes / warnings

- Alpaca historical corporate-action data may be revised or may include future-known records unless an as-of or announcement timestamp is available.
- Pre-ex-date sleeves are invalid without a timestamp proving the event was known before the trade.
- Post-ex-date sleeves still need explicit dividend/price-adjustment accounting and an as-of-safe event record before evaluation.
