# AR-065 Evaluation — ETF realized-volatility term-state breadth allocator

Created: 2026-06-26T12:11:25Z

## Safety / provenance
- Data source: Alpaca/qfa real market data via qfa AlpacaGateway.
- CSV: no CSV used; `--data-csv` not used.
- No daemon, no orders, no live trading.
- Temporary SQLite DBs matched `/tmp/qfa-ar065-*.sqlite3` and deleted: True.

## Primary qfa run
- Symbols: SPY, QQQ, IWM, TLT, GLD, XLU, XLE, SHY
- Range: 2020-01-02 to 2025-12-15, daily bars
- qfa run id: 1
- Pre-cost metrics: Sharpe 0.54771488, annual return 0.05587574, annual vol 0.11046067, max drawdown -0.19442805, total return 0.38065111.
- Estimated after 5 bps one-way turnover cost: Sharpe 0.40444051, annual return 0.0393107, max drawdown -0.21048708.
- Mean one-way daily turnover: 0.12580745; annual cost drag estimate: 0.01585174.

## Random-window protocol
- Count: 8
- Median Sharpe pre-cost: 1.07297812
- P25 Sharpe pre-cost: 0.76787934
- Median Sharpe after estimated 5 bps turnover cost: 0.91479255
- P25 Sharpe after estimated 5 bps turnover cost: 0.58732363
- Positive after-cost Sharpe rate: 0.875

## Orthogonality
- Status: computed
- Max abs correlation: 0.63897729
- Pass max-corr <= 0.60: False

## Suggested decision
**REJECTED** — Rejected because random-window after-cost Sharpe distribution or orthogonality failed thresholds.

Bad-result policy: if rejected, no refinement/direct inversion/extension child is suggested.

See `latest.json` and `ar065_qfa_alpaca_real_20260626T121125Z.json` for full run IDs, random windows, curves, and correlation details.
