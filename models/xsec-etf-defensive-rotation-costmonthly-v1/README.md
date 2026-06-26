# xsec-etf-defensive-rotation-costmonthly-v1

AR-039 research-only qfa alpha. Implements monthly/cost-aware refinement of AR-016 ETF defensive rotation. `model.py` exposes `generate_signals(context)` and uses only qfa-provided OHLCV context.

Artifacts:
- `model.py` qfa-compatible signal model
- `config.yaml` parameters and risk controls
- `metadata.yaml` issue metadata
- `evaluations/latest.json` machine-readable result
- `evaluations/latest.md` human summary
- `evaluations/runs/20260626T020800Z_ar039_eval.json` immutable evaluation snapshot

Evaluation used Alpaca real data through qfa, never `--data-csv`, temporary SQLite only, no daemon, and no trades.
