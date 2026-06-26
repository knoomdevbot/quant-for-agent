# AR-072 Evaluation — beta/redundancy constrained macro drawdown allocator

Created: `2026-06-26T12:56:49Z`

## Decision

Suggested decision: **rejected**

Rejected: max absolute correlation to AR-037/AR-043 retained curves remained above 0.60, failing AR-072 orthogonality falsifier.

## Primary qfa/Alpaca backtest

Window: `2023-01-01` to `2025-12-31`. qfa pre-cost Sharpe `1.03872587`; external 5 bps Sharpe `0.87046827`; total return `0.14591345`; annualized return `0.04682723`; annualized vol `0.05426844`; max drawdown `-0.06977752`; win rate `0.484`; realized beta to SPY `0.18572898`.

20 bps stress-cost Sharpe `0.36499521`; total return `0.05624836`; max drawdown `-0.08297703`.

## Random/stress windows

Count `12`; median Sharpe `-0.16732405`; p25 Sharpe `-0.46501412`; worst Sharpe `-1.08485582`; positive-window rate `0.5`; worst max drawdown `-0.10797704`; median mean daily turnover `0.06153082`; median realized beta `0.13138326`.

## Orthogonality

Status: `failed_max_corr_gt_0_60_to_ar037_ar043`; max |corr| to AR-037/AR-043 `0.68326067`; max |corr| all checked `0.89139175`. Method: Pearson correlation of overlapping daily cost-adjusted equity returns from retained run JSON artifacts.

- `AR-063_parent` corr `0.89139175` over `749` periods: `/Users/moonk/quant-for-agent/models/macro-surprise-drawdown-etf-allocator-v1/evaluations/runs/ar063_qfa_alpaca_real_20260626T115805Z.json`
- `AR-063_parent` corr `0.89139175` over `749` periods: `/Users/moonk/quant-for-agent/models/macro-surprise-drawdown-etf-allocator-v1/evaluations/runs/ar063_qfa_alpaca_real_20260626T115707Z.json`
- `AR-037` corr `0.68326067` over `738` periods: `/Users/moonk/quant-for-agent/models/etf-carry-defensive-allocation-v1/evaluations/runs/ar037_qfa_alpaca_real_20260626T083545Z.json`
- `watchlist` corr `0.67536907` over `738` periods: `/Users/moonk/quant-for-agent/models/etf-carry-defensive-turnover-brake-v1/evaluations/runs/ar060_qfa_alpaca_real_20260626T112748Z.json`
- `watchlist` corr `0.64880873` over `738` periods: `/Users/moonk/quant-for-agent/models/etf-carry-defensive-orthogonal-v1/evaluations/runs/ar049_qfa_alpaca_real_20260626T102842Z.json`
- `watchlist` corr `0.62100839` over `499` periods: `/Users/moonk/quant-for-agent/models/etf-defensive-momentum-carry-rotation-v1/evaluations/runs/ar059_qfa_alpaca_real_20260626T112909Z.json`
- `AR-043` corr `0.55344905` over `738` periods: `/Users/moonk/quant-for-agent/models/etf-stress-liquidity-volume-v1/evaluations/runs/ar043_qfa_alpaca_real_20260626T094720Z.json`
- `watchlist` corr `0.52475597` over `738` periods: `/Users/moonk/quant-for-agent/models/etf-stress-recovery-halflife-v1/evaluations/runs/ar055_qfa_alpaca_real_20260626T111206Z.json`
- `AR-008` corr `0.45838397` over `738` periods: `/Users/moonk/quant-for-agent/models/risk-off-crossasset-randomcost-v1/evaluations/runs/ar025_qfa_alpaca_real_20260626T081003Z.json`
- `AR-008` corr `0.44957608` over `499` periods: `/Users/moonk/quant-for-agent/models/risk-off-crossasset-switch-v1/evaluations/runs/qfa_realdata_20240101_20251231_run1.json`

## Controls

- data_source: Alpaca real daily market data via qfa/AlpacaGateway only
- no_csv_used: true
- no_data_csv_argument_used: true
- no_daemon: true
- no_orders: true
- db_artifact_retained: false
- raw_daily_paths_retained: false

Command provenance: credentials were sourced from the configured Alpaca profile secret file with values redacted; qfa backtest was run with model path, symbols, daily timeframe, initial cash, and a temporary SQLite DB; no `--data-csv`, daemon, or order commands were used.
