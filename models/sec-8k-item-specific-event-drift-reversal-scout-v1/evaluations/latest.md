# AR-145 evaluation result — SEC 8-K feasibility scout

- Run ID: `ar145_sec_feasibility_20260629T181002Z`
- Decision: **rejected / completed feasibility rejected**
- Performance metrics: `null` (no market-data performance run)
- Provenance booleans: no CSV, no `data_csv`, no daemon, no orders, no retained raw daily paths

## SEC metadata probe

SEC public endpoints were reachable with a polite user-agent. The bounded probe used `company_tickers.json` and 100 corresponding `submissions/CIK*.json` requests.

Aggregate counts:

- Company ticker entries available: 10,433
- Submissions attempted: 100
- Submission errors: 0
- Recent 8-K filings: 6,967
- Recent 8-K filings with `items`: 6,967
- Recent 8-K filings with `acceptanceDateTime`: 6,967
- Recent 8-K filings with `items`, `acceptanceDateTime`, accession number, and primary document: 6,967
- Item 2.02 8-K filings: 2,248
- Issuers with Item 2.02 in the bounded sample: 77

## Interpretation

The required metadata fields appear feasible for building an event table, but the run was intentionally bounded and did not fetch Alpaca/qfa bars, calculate returns, test controls, or retain raw filings/bars. The idea is therefore rejected for this cycle rather than promoted to watchlist: there is no alpha-performance evidence, only source-feasibility evidence.
