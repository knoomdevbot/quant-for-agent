# AR-078 intraday Treasury announcement reversion

Research artifacts for `intraday-treasury-announcement-reversion-v1`.

## Hypothesis

Treasury ETFs may overreact around explicit intraday macro announcements and partially mean-revert over the next intraday window, producing a stream distinct from AR-070's daily event-gated curve-shock model.

## Implementation

- Universe: SHY, IEF, TLT, TIP, LQD, HYG, GLD, SPY.
- Data requirement: Alpaca/qfa real 1-minute OHLCV only; no CSV.
- Event timestamps: explicit public FOMC statement timestamps at 14:00 New York time and CPI releases at 08:30 New York time, converted to UTC.
- Signal: measure IEF/TLT duration shock from event timestamp to `event + 60 minutes`, then hold a reversal basket for 60 minutes.
- Safety: `model.py` returns zero weights unless `context.metadata` supplies valid event timestamp metadata. This avoids substituting daily AR-070 logic in ordinary qfa backtests.

## Evaluation result

Rejected. Alpaca real 1-minute evaluation across 59 FOMC/CPI events from 2023-01-12 to 2025-12-10 was negative after 5, 10, and 20 bps one-way cost proxies. qfa can run 1-minute bars, but its CLI has no native event-metadata/calendar argument, so the durable model is inert without explicit event metadata.

See `evaluations/latest.md` and `evaluations/latest.json` for metrics.
