# AR-149 latest evaluation

**Decision:** hold / source-gated.

Publication timing was documented: NY Fed Primary Dealer Statistics are updated Thursdays at approximately 4:15 p.m. ET with the previous week's statistics.  However, the scout could not document revision/vintage safety: the checked API/docs expose current historical time series, as-of lists, series breaks, and by-as-of pulls, but not point-in-time vintages, release timestamps per observation, or revision-history metadata.

Performance metrics are intentionally `null`; Alpaca/qfa ETF OHLCV was not used after the source gate failed.  No CSV, no `--data-csv`, no daemon, and no orders were used.  The model emits flat weights.

See `latest.json` and `evaluations/runs/ar149_source_gate_20260629T212403Z.json` for compact provenance.
