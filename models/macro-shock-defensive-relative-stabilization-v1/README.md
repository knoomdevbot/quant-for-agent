# Macro-shock defensive relative stabilization v1

Rule-based, event-gated ETF allocator for AR-122. It activates only after timestamp-safe daily OHLCV shock conditions and ranks defensive/low-beta sleeves by relative stabilization versus cyclicals.

Decision: **rejected** after compact Alpaca real-data evaluation. See `evaluations/latest.md` and `evaluations/latest.json`.

Safety: no CSV, no `--data-csv`, no daemon, no orders; raw daily bars are not retained.
