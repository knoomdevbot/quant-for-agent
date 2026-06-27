# AR-063 Evaluation — macro-surprise drawdown ETF allocator

Created: `2026-06-26T11:58:05Z`

## Decision

Suggested decision: **watchlist**

Watchlist: positive median random/stress-window Sharpe after costs and tolerable drawdown, but p25/orthogonality evidence is not strong enough for acceptance.

## Primary qfa/Alpaca backtest

Window: `2023-01-01` to `2025-12-31`. qfa pre-cost Sharpe `0.98361468`; external 5 bps turnover-cost Sharpe `0.66950757`; annualized return `0.05039287`; annualized vol `0.07798218`; max drawdown `-0.11282729`; win rate `0.484`.

## Random/stress windows

Count `12`; median Sharpe `0.10493538`; mean Sharpe `0.16731383`; p25 Sharpe `-0.0645293`; worst Sharpe `-0.83906287`; positive-window rate `0.58333333`; worst max drawdown `-0.1435906`; median mean daily turnover `0.15944223`.

## Orthogonality

Status: `computed`. Method: Pearson correlation of overlapping daily cost-adjusted equity returns from retained run JSON artifacts.

- `AR-037` corr `0.69386667` over `738` periods: `/Users/moonk/quant-for-agent/models/etf-carry-defensive-allocation-v1/evaluations/runs/ar037_qfa_alpaca_real_20260626T083545Z.json`
- `AR-043` corr `0.68230752` over `738` periods: `/Users/moonk/quant-for-agent/models/etf-stress-liquidity-volume-v1/evaluations/runs/ar043_qfa_alpaca_real_20260626T094720Z.json`
- `watchlist` corr `0.65832471` over `738` periods: `/Users/moonk/quant-for-agent/models/etf-stress-recovery-halflife-v1/evaluations/runs/ar055_qfa_alpaca_real_20260626T111206Z.json`
- `watchlist` corr `0.63089623` over `499` periods: `/Users/moonk/quant-for-agent/models/etf-defensive-momentum-carry-rotation-v1/evaluations/runs/ar059_qfa_alpaca_real_20260626T112909Z.json`
- `watchlist` corr `0.58369545` over `738` periods: `/Users/moonk/quant-for-agent/models/etf-carry-defensive-turnover-brake-v1/evaluations/runs/ar060_qfa_alpaca_real_20260626T112748Z.json`
- `watchlist` corr `0.56643239` over `738` periods: `/Users/moonk/quant-for-agent/models/etf-carry-defensive-orthogonal-v1/evaluations/runs/ar049_qfa_alpaca_real_20260626T102842Z.json`
- `AR-008` corr `0.54660189` over `499` periods: `/Users/moonk/quant-for-agent/models/risk-off-crossasset-switch-v1/evaluations/runs/qfa_realdata_20240101_20251231_run1.json`
- `AR-008` corr `0.52763769` over `738` periods: `/Users/moonk/quant-for-agent/models/risk-off-crossasset-randomcost-v1/evaluations/runs/ar025_qfa_alpaca_real_20260626T081003Z.json`
- `watchlist` corr `0.46359315` over `499` periods: `/Users/moonk/quant-for-agent/models/tsmom-voltarget-liquid-etf-randomcost-v1/evaluations/runs/qfa_real_alpaca_ar015_20260626T072547Z.json`
- `AR-051` corr `0.36962363` over `500` periods: `/Users/moonk/quant-for-agent/models/xsec-etf-defensive-rotation-orthogonal-v1/evaluations/runs/ar051_qfa_alpaca_real_20260626T102756Z.json`

## Controls

- no_csv_used: true
- no_data_csv_argument_used: true
- no_daemon: true
- no_orders: true

Command provenance: credentials, if present, were sourced from the configured Alpaca profile secret file with values redacted; qfa backtest was run against Alpaca real daily bars without `--data-csv`, daemon, or order commands.
