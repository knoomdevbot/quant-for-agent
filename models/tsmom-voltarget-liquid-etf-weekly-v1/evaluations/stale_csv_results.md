# Stale CSV-derived results

The following artifacts were produced from local CSV fixture data before the real-data Alpaca-backed AR-003 evaluation. They are retained only for provenance/smoke-test compatibility and are **stale** for alpha research decisions.

- `models/tsmom-voltarget-liquid-etf-weekly-v1/evaluations/runs/qfa_smoke_20260626T012301Z.json`
  - Reason: AAPL/MSFT four-row fixture smoke test, not the intended ETF universe.
- prior `models/tsmom-voltarget-liquid-etf-weekly-v1/evaluations/latest.json` / `latest.md` CSV fixture summaries
  - Reason: overwritten by the current real-data Alpaca-backed latest evaluation.

Current latest evaluation uses qfa Alpaca real market data without `--data-csv`:

- `models/tsmom-voltarget-liquid-etf-weekly-v1/evaluations/latest.json`
- `models/tsmom-voltarget-liquid-etf-weekly-v1/evaluations/latest.md`
- `models/tsmom-voltarget-liquid-etf-weekly-v1/evaluations/runs/qfa_real_alpaca_20260626T055000Z.json`
