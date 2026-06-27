# vixy-tlt-stress-carry-etf-v1 (AR-052)

Divergent child of AR-039. This model tests whether a liquid ETF volatility-stress/carry proxy can produce a return stream distinct from a defensive price-momentum rotation.

## Signal design

- Universe: `VIXY, TLT, IEF, SHY, SPY`.
- Stress proxy: combines SPY drawdown, recent SPY loss, SPY realized-volatility acceleration, SPY range expansion, and short-horizon VIXY jumps.
- VIXY sleeve: capped at 12% and activated only when stress is elevated; 60-day VIXY decay/carry and high VIXY volatility reduce exposure.
- Duration sleeve: allocates to `TLT`/`IEF` based on stress and duration trend, with volatility penalties.
- Fallback/risk sleeve: `SHY` absorbs unused risk; modest `SPY` exposure remains in benign regimes to offset defensive carry drag.

## Research constraints

- QFA-compatible `generate_signals(context)` only.
- Alpaca real daily OHLCV through qfa/AlpacaGateway only; no CSV data and no `--data-csv`.
- No daemon, no live trading, no order placement.
- Native qfa backtest has no transaction-cost field; evaluations apply a post-run 5 bps one-way turnover cost proxy.
- Temporary SQLite DBs use `/tmp/qfa-AR-052-*.sqlite3` and are deleted after JSON capture.

## Evaluation status

Suggested decision: **rejected**. Primary full-period post-cost Sharpe was negative and the random-window lower tail was poor despite a positive median random-window Sharpe.

See:

- `evaluations/latest.json`
- `evaluations/latest.md`
- immutable run bundle under `evaluations/runs/`
