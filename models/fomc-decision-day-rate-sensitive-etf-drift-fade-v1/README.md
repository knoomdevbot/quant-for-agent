# FOMC decision-day rate-sensitive ETF drift/fade v1

AR-130 event-study model. The rule is intentionally timestamp-safe and public-calendar-only: hold an equal-weight long basket of TLT, IEF, SHY, LQD, HYG, GLD, SPY, QQQ, XLF, and XLRE on hardcoded scheduled FOMC decision dates; otherwise hold cash/zero exposure.

The selected universe was fixed before performance review from the core candidate pool using Alpaca/qfa coverage, liquidity, and economic exposure. Optional TIP/UUP/XLU had clean coverage but were excluded before return review to avoid expanding the basket post hoc.

Evaluation used qfa/Alpaca real daily OHLCV via configured paper-data access. No CSV or `--data-csv` was used; no daemon was run; no orders were placed; raw bars and daily equity curves were not retained.

Suggested decision: **reject**. The primary prior-close-to-decision-close leg failed the predeclared gates at 10 bps one-way costs: negative median event return, hit rate below 55%, weak placebo rank, negative p25, and failure after calendar-overlap exclusions.

See `evaluations/latest.md` and `evaluations/latest.json` for compact metrics.
