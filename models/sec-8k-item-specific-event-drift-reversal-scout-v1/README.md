# SEC 8-K item-specific event drift/reversal scout v1

AR-145 is a feasibility-first scout for using timestamped SEC 8-K item metadata, especially Item 2.02 earnings-results filings, as event anchors for later drift/reversal tests in liquid U.S. common stocks.

## Current decision

**Blocked.** A bounded recovery run confirmed that SEC public submissions metadata exposes 8-K `form`, `items`, and `acceptanceDateTime` fields for a deterministic large-cap sample, but it did not demonstrate the required broad, timestamp-safe liquid event table. No qfa/Alpaca market backtest was run, and performance metrics are intentionally null.

## Model behavior

`model.py` exposes the required qfa-compatible `generate_signals(context)` function and returns `{}` / cash. It must remain cash-only until a timestamp-safe event table is implemented and passes feasibility gates.

## Bounded sample and counts

Attempted symbols: AAPL, MSFT, AMZN, NVDA, META, GOOGL, JPM, XOM, WMT, UNH, BRK-B, LLY.

Aggregate SEC metadata counts from the bounded run:

- company ticker mappings: 10,433
- submissions endpoints attempted/succeeded: 12/12
- recent filings inspected: 36,305
- recent 8-K filings: 743
- recent 8-K with item tags: 743
- recent 8-K with acceptance timestamps: 743
- recent 8-K including Item 2.02: 262
- target gate before performance: at least 300 liquid Item 2.02 events across a broad timestamp-safe sample

## Limitations

- No point-in-time CIK/ticker history was built.
- Current SEC ticker mapping can introduce survivorship and ticker-change bias.
- The sample is deterministic and intentionally small to avoid long network calls.
- No raw event table is retained; only compact aggregate counts are stored.
- No market bars, qfa daemon, orders, or CSV-backed data were used.

## Artifacts

- `model.py` — qfa contract, cash-only.
- `config.yaml` and `metadata.yaml` — bounded feasibility configuration/provenance.
- `evaluations/latest.json` and `evaluations/latest.md` — compact latest result.
- `evaluations/runs/ar145_feasibility_20260629T171241Z.json` — run-level counts and decision.
