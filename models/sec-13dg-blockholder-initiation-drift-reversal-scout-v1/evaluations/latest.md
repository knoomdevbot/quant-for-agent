# AR-146 Evaluation Result

- Run ID: `ar146_sec_13dg_feasibility_20260629T203501Z`
- Decision: **rejected / completed feasibility-only**
- Source gate passed: **false**
- Performance metrics: `null` (no market-data backtest run)

## Compact SEC probe

- SEC endpoint status: ok
- `company_tickers.json` entries: 10,433
- Sample: first 100 SEC current ticker-mapping entries
- Submissions attempted/errors: 100 / 0
- Recent 13D/13G-family filings: 2,711
- Initial `SC 13D`/`SC 13G` filings: 482
- Amendment filings: 2,229
- With acceptance timestamps/accessions/primary docs: 2,711 / 2,711 / 2,699
- Sampled issuers with initial 13D/13G: 72

## Rationale

SEC public metadata is reachable and contains timestamped Schedule 13D/13G-family form records, but the bounded recovery did not safely complete AR-146's stricter feasibility gate: no retained raw event table, robust primary-document parser, ownership fields, filer/group classification, historical ticker mapping, common-stock liquidity screen, or issuer/filer/date concentration validation. No CSV/backtest data, daemon, or orders were used.

The scout is therefore inert: `generate_signals(context)` returns `{}`.
