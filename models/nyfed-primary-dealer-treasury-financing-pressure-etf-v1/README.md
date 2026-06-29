# AR-149 — NY Fed primary dealer Treasury financing-pressure duration ETF scout

Decision: **hold / source-gated**.

## What was checked

- NY Fed Markets API documentation (`markets-api.yml`) exposes Primary Dealer Statistics endpoints for time-series definitions, as-of dates, series breaks, by-as-of survey pulls, and by-series pulls.
- The NY Fed Primary Dealer Statistics page documents that the data tool is updated on Thursdays at approximately 4:15 p.m. ET with the previous week's statistics and that history starts January 28, 1998.
- Series-break metadata are machine-readable and currently identify six structural regimes: `SBP2001`, `SBP2013`, `SBN2013`, `SBN2015`, `SBN2022`, and `SBN2024`.

## Source gate result

The publication timing component is adequate for a rule that trades no earlier than the next session after the Thursday 4:15 p.m. publication.  The revision/vintage component is not adequate: the API endpoints checked did not expose point-in-time vintages, per-observation release timestamps, or revision-history metadata, and the public page did not provide an explicit no-revision guarantee suitable for historical trading research.

Because the source/vintage gate failed first, no Alpaca/qfa ETF performance backtest was accepted for this scout. Configured market-data access was not used for a successful OHLCV request. No CSV, daemon, or order path was used.

## Production behavior

`model.py` intentionally returns flat weights for the selected duration ETF universe (`TLT`, `IEF`, `IEI`, `SHY`, `GOVT`) to prevent accidental trading on potentially revised historical dealer-statistics data.

## Next step

Do not queue direct children from this source-gated result.  Revisit only if NY Fed or another archival source can provide point-in-time snapshots/revision history for Primary Dealer Statistics, or an explicit revision policy strong enough to justify use of current historical API values.
