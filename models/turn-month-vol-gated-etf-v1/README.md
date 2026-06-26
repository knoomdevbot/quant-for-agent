# turn-month-vol-gated-etf-v1

AR-041 research-only qfa alpha refining AR-021 with a SPY realized-volatility/trend/drawdown gate. `model.py` exposes `generate_signals(context)` and uses only qfa-provided OHLCV context.

Artifacts:
- `model.py` qfa-compatible signal model
- `config.yaml` parameters and risk controls
- `metadata.yaml` issue/evaluation metadata
- `evaluations/latest.json` machine-readable result
- `evaluations/latest.md` human summary
- `evaluations/runs/ar041_qfa_real_alpaca_20260626T094208Z.json` immutable evaluation snapshot

Evaluation used Alpaca real market data through qfa, never `--data-csv`, temporary SQLite DBs under `/tmp`, no daemon, and no trades. Suggested decision: `reject_falsified_by_lower_tail_or_parent_comparison`.
