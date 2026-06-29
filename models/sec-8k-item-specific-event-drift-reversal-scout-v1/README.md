# SEC 8-K item-specific event drift/reversal feasibility scout (AR-145)

Decision: **rejected / feasibility-only**.

This bounded recovery run did not test alpha performance. It only checked whether SEC public metadata can support a timestamp-safe Item 2.02 8-K event table. The SEC endpoints were reachable with a polite user-agent, and a deterministic 100-entry company ticker sample showed that recent submissions JSON includes `form`, `items`, `acceptanceDateTime`, accession number, and primary-document fields.

## Probe summary

- Source: SEC `company_tickers.json` plus bounded `data.sec.gov/submissions/CIK*.json` requests.
- Sample: first 100 entries from SEC ticker mapping sorted by numeric key; this is a liquid/large-cap-leaning mapping sample but was not independently screened for all common-stock edge cases.
- Recent 8-K filings observed: 6,967.
- Recent 8-K filings with `items`: 6,967.
- Recent 8-K filings with `acceptanceDateTime`: 6,967.
- Recent 8-K filings with `items`, `acceptanceDateTime`, accession number, and primary document: 6,967.
- Item 2.02 8-K filings observed: 2,248 across 77 issuers.

## Why rejected for this cycle

The event metadata appears feasible, but this run intentionally retained no raw filings or bars and ran no qfa/Alpaca performance evaluation. Without timestamp-safe market bars, matched controls, shifted-label checks, and breadth/concentration diagnostics over the actual tradable universe, there is no evidence of an alpha edge. The model is therefore inert and returns no signals.
