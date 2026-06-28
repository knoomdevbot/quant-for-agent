# AR-139 — SEC XBRL quarterly fundamental inflection cross-sectional allocator

## Decision

Blocked / rejected before portfolio backtest.

The alpha requires timestamp-safe SEC 10-Q/10-K XBRL companyfacts. The SEC endpoints were reachable and broad, but the companyfacts endpoint available in this run is a current compiled view, not a historical as-of snapshot. It includes per-fact `filed` dates, yet later filings/amendments can revise or add facts for old fiscal periods. Using today's endpoint to reconstruct what was known at old filing dates would therefore risk hindsight. The issue explicitly says to block rather than fabricate point-in-time facts if reconstruction is unsafe.

## Probe performed

- Queried SEC `company_tickers.json`: 10,433 rows.
- Applied a rough name/ticker filter excluding obvious ETFs/funds/trusts/ADRs/preferreds/warrants/units: 9,213 common-like rows.
- Sampled 40 liquid major common-stock tickers from SEC companyfacts.
- The sample had 50,029 current-endpoint filing fact entries across intended tags, and all 40 sample names had at least 8 fiscal-period keys.
- The same endpoint also showed multiple filed/accession observations for identical old tag/unit/fiscal-period/end-date keys, e.g. NVDA FY 2009 revenues filed in 2010 and again in 2011; CRM FY 2019 revenue filed in 2020 and again in 2021; T Q2 2013 revenues filed twice in 2014; DIS FY 2021 assets repeated across 2022 filings. This confirms restatement/amendment handling is material.

## Universe and limitations

No selected trading universe was formed. The intended broad U.S. common-stock universe and qfa/Alpaca liquidity filters were not evaluated because the fundamental signal failed the point-in-time prerequisite first. Current-endpoint observation counts are recorded only as a reachability/structure probe, not as accepted timestamp-safe filing observations.

## Runtime model

`model.py` exposes `generate_signals(context)`. It returns normalized externally supplied `ar139_pit_signals` only if the runtime context/metadata provides already point-in-time-safe signals. Otherwise it safely returns zero weights for visible symbols.

## Provenance / safety

SEC public endpoints were queried with a generic research User-Agent. No CSV-backed market data, `--data-csv`, qfa daemon, orders, credential printing, or credential persistence were used. Raw daily paths, fact arrays, and caches were not retained.
