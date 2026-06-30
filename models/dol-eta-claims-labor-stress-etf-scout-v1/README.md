# DOL/ETA Claims Labor-Stress ETF Scout v1

Issue: AR-151

## Decision

**Source-vintage feasibility: passed in principle; performance not evaluated.**

This bounded recovery pass focused on the hard source gate. It did not run a qfa daemon, place orders, use CSV market data, or run a long performance backtest.

## Source-gate findings

- The official DOL/ETA weekly claims landing page is available and links the current weekly claims release.
- The DOL/ETA weekly claims archive links to the DOL newsroom ETA release archive.
- The DOL newsroom archive exposes dated `etaYYYYMMDD` pages titled "Unemployment Insurance Weekly Claims Report". These pages provide a release-date mapping suitable for point-in-time processing if a later ETL stores each dated release payload and trades only after public release.
- The latest DOL weekly claims PDF is reachable from the official site.
- ALFRED exposes an archival page for the FRED initial-claims series with vintage/revision context, but the programmatic vintage API path was not used in this recovery pass because it requires an external credential.

The source gate is therefore not falsified by revised-data lookahead: the official dated release archive can be used as the primary point-in-time source. However, no durable parser and no real ETF performance test were completed here, so the model remains disabled.

## Trading / evaluation status

- Model wrapper returns zero weights for the selected ETF universe.
- Performance metrics are unavailable/null.
- No raw daily market-data paths are retained.
- No children were created.

## Selected ETF universe for future evaluation

SPY, QQQ, IWM, XLK, XLF, XLU, XLP, TLT, IEF, SHY, HYG, LQD, GLD.
