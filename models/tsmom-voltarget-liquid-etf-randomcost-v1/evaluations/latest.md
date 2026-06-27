# AR-015 Evaluation - tsmom-voltarget-liquid-etf-randomcost-v1

Created: 2026-06-26T07:25:47Z

## Result
Suggested decision: **watchlist**. Random-window costed validation did not trigger the AR-015 falsifier: 5 bps costed median Sharpe is 0.52258623 with 84.615385% positive windows and p25 Sharpe 0.11562103. Not accepted yet because turnover is material (median avg daily turnover 0.08285866; main annualized turnover proxy 21.00185571), qfa lacks native cost/slippage modeling, worst random costed Sharpe is -0.51612569, and orthogonality evidence is limited.

## Main qfa real-data run
- Data: Alpaca real bars via qfa/AlpacaGateway, no CSV, no `--data-csv`, no daemon, no trades.
- Symbols: SPY, QQQ, IWM, TLT, GLD, SLV, USO, FXE, FXY
- Window: 2024-01-01 to 2025-12-31; qfa run id 1 in temp DB `/tmp/qfa-ar015-98477.sqlite3` (removed).
- Pre-cost metrics: Sharpe 1.21599641, total return 0.33163486, annualized return 0.15528762, annualized vol 0.12518939, max drawdown -0.09362303, win rate 0.426, periods 500.

## Cost/turnover sensitivity
- qfa native costs: unavailable; external turnover haircut applied.
- 1 bps costed Sharpe: 1.19936887
- 5 bps costed Sharpe: 1.13279897
- 10 bps costed Sharpe: 1.0494581
- Main avg daily turnover: 0.0833407 (annualized proxy 21.00185571)

## Random-window protocol
- Windows: 26 deterministic pseudo-random/stress windows, seed 15015.
- Pre-cost Sharpe median/p25/worst/positive-rate: 0.60770853 / 0.16801065 / -0.43842839 / 0.92307692
- 5 bps costed Sharpe median/p25/worst/positive-rate: 0.52258623 / 0.11562103 / -0.51612569 / 0.84615385
- Worst costed max drawdown: -0.29365532
- Median avg daily turnover: 0.08285866

## Parameter grid
Best five by random8 costed median Sharpe are stored in `latest.json`; best params: `{'lookback_days': 252, 'max_abs_weight': 0.35, 'min_periods': 253, 'target_vol': 0.1, 'vol_window': 20}` with random8 costed median Sharpe 0.70135321 and main costed Sharpe 1.77806054.

## Orthogonality
Attempted from retained latest.json equity curves; results count: 1. See JSON.

## Suggested children
- Refinement: Monthly/weekly held 252-day ETF TSMOM variant with explicit no-trade bands to reduce turnover, then rerun the same Alpaca random-window 5-10 bps cost protocol.
- Divergent: ETF carry/term-structure defensive allocation using dividend/yield/curve proxies and monthly rebalancing, not price time-series momentum.

## Artifacts
- Immutable run JSON: `models/tsmom-voltarget-liquid-etf-randomcost-v1/evaluations/runs/qfa_real_alpaca_ar015_20260626T072547Z.json`
- Latest JSON: `models/tsmom-voltarget-liquid-etf-randomcost-v1/evaluations/latest.json`
