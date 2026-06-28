# Commodity ETF Roll-Proxy Allocator v1 (AR-137)

Decision: **rejected** after strict real-data fast falsification.

## Model

`model.py` exposes `generate_signals(context) -> dict[str, float]`. It is a long-only non-levered commodity ETF allocator over:

USO, USL, BNO, UNG, UNL, GLD, IAU, SLV, CPER, DBB, DBA, CORN, WEAT, SOYB, DBC, PDBC, COMT, GSG.

The signal uses only lagged daily close history supplied in `context`:

- 120-day within-family relative return rank as a noisy ETF roll/term-structure proxy.
- 60-day and 120-day trend confirmation.
- 60-day realized-volatility sizing.
- Long-only cash-allowed weights with 15% symbol cap and 35% sleeve cap.

## Evaluation

Evaluation used qfa `AlpacaGateway` real daily OHLCV with configured paper-data access and credential values redacted. No CSV, no `--data-csv`, no qfa daemon, and no orders were used. No raw daily bars, equity curves, daily return arrays, or weight tails are retained.

Primary run: `evaluations/runs/ar137_qfa_alpaca_real_20260628T045621Z.json`.

Key after-cost combined-signal results at 10 bps one-way turnover cost:

- Full-period Sharpe: 0.4047
- Full-period annualized return: 0.0557
- Full-period annualized volatility: 0.1688
- Full-period max drawdown: -0.3804
- Random windows: 40 two-year windows
- Median window Sharpe: 0.2779
- P25 window Sharpe: -0.0398
- Worst window Sharpe: -0.7407
- Positive-window rate: 0.7000
- Mean daily turnover: 0.0638
- Activation rate: 0.9526

Rejected because the combined roll-proxy allocator did not beat simple controls on robustness: equal-weight commodity basket median Sharpe 0.7382, GLD buy-hold median Sharpe 0.7380, USO buy-hold median Sharpe 0.5935, trend-only median Sharpe 0.4274, and commodity ETF TSMOM median Sharpe 0.4519. Approximate max absolute control correlation was 0.9432, indicating low orthogonality to simple trend controls.
