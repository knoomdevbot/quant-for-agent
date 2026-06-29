# index-add-delete-announcement-drift-v1 (AR-141)

Decision: **blocked** at the event-source gate.

AR-141 required a broad ex-ante pool of U.S. common-stock S&P 500, Nasdaq-100, and Russell 1000 / large-cap addition/deletion **public announcement** records, usable only after a conservative announcement lag. The hard gate was at least 150 timestamp-safe liquid common-stock events before any return scoring.

## Source scout

I checked public index-membership sources before any market backtest:

- Wikipedia `List of S&P 500 companies`: current constituents plus a historical change table with about 400 effective-date rows. It does not provide a separate announcement timestamp column.
- Wikipedia `Nasdaq-100`: current constituents plus a historical change table with about 225 effective-date rows. It does not provide a separate announcement timestamp column.
- Wikipedia `Russell 1000 Index`: current constituents only in the parsed public tables; no historical addition/deletion announcement table.
- S&P Global public index page/news area: direct request returned HTTP 403 in this environment.

These sources are useful for effective-date membership changes, but the issue explicitly rejects deterministic rebalance/effective-date proxies unless true timestamp-safe announcement records are available. I therefore did not run a qfa/Alpaca return backtest.

## Evaluation status

- Event-source gate: **failed**; timestamp-safe events acquired: 0.
- Minimum required: 150.
- Market data: not queried, because the event-source gate failed first.
- CSV-backed market data: not used.
- qfa daemon/orders: not used.

## What would unblock this

A durable event archive with, for each event, index family, add/delete side, common-stock identifier/ticker at the time, public announcement date/time or timestamp-safe publication date, effective date, and reproducible source URL. Candidate sources may include licensed S&P/Nasdaq/FTSE Russell corporate-actions or index-announcement feeds, or a reproducible archived press-release scrape with publication timestamps and symbol mapping.
