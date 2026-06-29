# SEC 13D/13G blockholder initiation drift/reversal scout v1

AR-146 was completed as a bounded source-gate feasibility scout, not a performance backtest.

## Decision

Rejected / completed feasibility-only. SEC public endpoints were reachable and recent submissions metadata exposes Schedule 13D/13G-family form names, acceptance timestamps, accession numbers, and primary documents in a deterministic 100-issuer sample. However, the bounded recovery did not safely build the required timestamp-safe parsed event table with subject issuer/filer fields, ownership percentages, initial-vs-amendment validation, historical ticker mapping, liquid common-stock filters, or concentration diagnostics.

## Probe

- Source: SEC `company_tickers.json` and `submissions/CIK##########.json` public endpoints.
- Sample: first 100 entries from SEC company_tickers sorted by numeric key.
- Compact aggregate counts only; no raw filing/event table or market bars retained.
- No CSV files, qfa daemon, orders, or Alpaca/qfa performance data used.

## Result

The sample contained 2,711 recent 13D/13G-family filings, including 482 non-amended `SC 13D`/`SC 13G` forms across 72 sampled issuers. This suggests the SEC metadata source is reachable, but it is insufficient to pass AR-146's stricter source gate without robust parsing and survivorship-safe mapping. `generate_signals(context)` therefore returns an empty dict.
