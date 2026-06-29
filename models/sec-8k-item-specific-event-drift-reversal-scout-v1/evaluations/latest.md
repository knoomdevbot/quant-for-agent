# AR-145 latest evaluation — feasibility blocked

- **Run:** `ar145_feasibility_20260629T171241Z`
- **Decision/status:** blocked; feasibility gate failed; no performance backtest run.
- **Data source:** SEC public company-tickers and submissions metadata only.
- **No CSV / daemon / orders:** `no_csv_used=true`, `no_data_csv_argument_used=true`, `no_daemon=true`, `no_orders=true`, `raw_daily_paths_retained=false`.

## Bounded SEC metadata check

Deterministic liquid large-cap sample: AAPL, MSFT, AMZN, NVDA, META, GOOGL, JPM, XOM, WMT, UNH, BRK-B, LLY.

Short-timeout SEC requests succeeded for company tickers and all 12 submissions endpoints. Recent submissions expose `form`, `items`, and `acceptanceDateTime`, so the metadata fields exist, but this recovery run did not construct a timestamp-safe broad liquid event table.

Key counts:

- SEC company ticker mappings returned: 10,433
- Symbols requested / with submissions metadata: 12 / 12
- Recent filings inspected from submissions metadata: 36,305
- Recent 8-K filings in bounded sample: 743
- Recent 8-K filings with non-missing item tags: 743
- Recent 8-K filings with acceptance timestamps: 743
- Recent 8-K filings including Item 2.02: 262
- Feasibility target before performance work: at least 300 liquid Item 2.02 events across a broad timestamp-safe issuer/year/month sample

## Interpretation

The public SEC metadata path appears technically accessible and item-tagged, but the bounded 12-issuer sample did not demonstrate the required broad liquid Item 2.02 event universe. Current SEC ticker mapping is not point-in-time and can introduce survivorship/ticker-change bias. Because a timestamp-safe event table with liquid market-data coverage was not implemented, performance metrics are null/unavailable and orthogonality checks are deferred due to the feasibility gate.

## Required next work before any trading signal

Build a compact, point-in-time event table from SEC metadata with conservative acceptance-time lag, robust CIK/ticker history, common-stock/liquidity filters, issuer/year/month concentration checks, and qfa/Alpaca daily-bar coverage. Until then `model.py` returns `{}` / cash.
