# etf-flow-risk-breadth-regime-v1

AR-022 tested a non-calendar ETF allocation-pressure proxy: risk-on versus defensive ETF breadth, trend, and abnormal dollar-volume pressure. The model is qfa-compatible via `generate_signals(context)` and uses only OHLCV bars supplied by qfa/Alpaca.

## Result
Rejected. Main 2021-2025 qfa/Alpaca backtest Sharpe was -0.0242 with total return -5.40%; seven random subwindows had median Sharpe -0.1867. Metrics are pre-cost because qfa currently lacks native transaction-cost/slippage support.

## Artifacts
- `model.py`
- `config.yaml`
- `metadata.yaml`
- `evaluations/latest.json`
- `evaluations/latest.md`
- `evaluations/runs/qfa_real_alpaca_ar022_20260626T080049Z.json`

No daemon was run and no trades were placed. Because this was rejected, no refinement, inversion, or extension child is proposed.
