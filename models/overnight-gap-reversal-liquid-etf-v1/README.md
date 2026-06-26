# overnight-gap-reversal-liquid-etf-v1

Research artifact for **AR-012 — AR-002 divergent: liquid ETF overnight gap reversal**.

This folder contains a qfa-compatible model plus real Alpaca market-data evaluation artifacts. The intended strategy observes the current daily open relative to the prior close and fades large normalized gaps for the same regular session open-to-close hold.

## Files

- `model.py` — qfa `generate_signals(context)` implementation; research-only and never places orders.
- `config.yaml` — universe, parameters, protocol, and cost assumptions.
- `metadata.yaml` — issue/model metadata.
- `evaluations/latest.json` and `evaluations/latest.md` — latest real-data evaluation.
- `evaluations/runs/*.json` — retained run payloads.

## Important qfa limitation

The current qfa daily backtester calls `generate_signals` after the latest daily bar is complete and applies weights to the next close-to-close return. The model therefore implements a lagged qfa proxy. The evaluation artifacts use direct Alpaca-backed OHLC retrieval to evaluate the intended same-day open-to-close signal without using CSV fixtures or placing trades.

## Latest result

Selected parameters from the real-data grid were `gap_z_window=60`, `entry_z=1.5`, `market_filter=true`. On Alpaca daily OHLC bars from 2021-01-01 to 2026-06-24, the intended open-to-close evaluation with a simple 5 bps-per-side cost model produced Sharpe **-0.8126**, total return **-38.72%**, max drawdown **-43.43%**, 461 event days, and median 30-random-window Sharpe **-0.3743**.

Decision: **rejected**. The qfa CLI real-data smoke did run successfully as a lagged close-to-close proxy using a temporary SQLite DB that was removed after extracting compact metrics (`db_artifact_retained=false`), but qfa's current CLI has no cost/slippage parameter and does not measure same-day open-to-close execution.
