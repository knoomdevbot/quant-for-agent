# tsmom-voltarget-liquid-etf-randomcost-v1

AR-015 refinement of AR-003 ETF time-series momentum.

## Model

The qfa-compatible model exposes `generate_signals(context)` and reads only `context.prices`. It computes positive-only medium-term ETF momentum, scales scores by realized volatility, gross-normalizes to 1.0, and caps single ETF weights.

Default universe: SPY, QQQ, IWM, TLT, GLD, SLV, USO, FXE, FXY.

Default parameters:
- lookback_days: 126
- vol_window: 20
- target_vol: 0.10
- max_abs_weight: 0.35
- min_periods: 127

## Evaluation

Real-data evaluation used Alpaca market data through qfa/AlpacaGateway only. No CSV input, no `--data-csv`, no daemon, and no trades.

Primary artifacts:
- `evaluations/latest.json`
- `evaluations/latest.md`
- immutable run JSON in `evaluations/runs/`

Current result: watchlist, not accepted for allocation yet. The 5 bps random-window median Sharpe is positive, but turnover/cost sensitivity and limited orthogonality support require further validation.
