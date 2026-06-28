# FINRA short-sale volume pressure reversal (AR-140)

**Decision:** rejected / blocked by universe-event gates.

## Protocol

- Source: FINRA Reg SHO daily short-sale-volume files plus configured Alpaca/qfa real daily OHLCV.
- Market-data constraint: no CSV market data and no `--data-csv` usage.
- Trading constraint: no daemon and no orders.
- Timestamp rule: FINRA file-date signals are delayed until the next trading session.
- Artifact policy: compact summaries only; raw daily records, raw short-volume rows, equity paths, and weight tails are not retained.

## Key result

The signal could not pass the issue's minimum breadth gates under the recorded filters.

- Candidate FINRA symbols with at least 400 file dates: 9,861.
- Selected liquid common stocks: 0.
- Event count: 0.
- Random-window metrics: unavailable/null because no active events survived.

## Decision rationale

Reject AR-140 in its current form. The failure is not a tradable negative Sharpe result; it is a timestamp-safe universe construction / security-master failure. Do not create a direct refinement child unless the follow-up uses a materially improved point-in-time common-stock mapping and liquidity universe.
