# AR-003 latest evaluation: real-data qfa Alpaca backtest

- Model: `tsmom-voltarget-liquid-etf-weekly-v1`
- Issue: `AR-003`
- Created UTC: `2026-06-26T05:50:00Z`
- Data source: qfa Alpaca market data path; **no `--data-csv` used**.
- Trading: none; daemon: not run.
- DB: `models/tsmom-voltarget-liquid-etf-weekly-v1/evaluations/qfa-real.sqlite3`
- Run JSON: `models/tsmom-voltarget-liquid-etf-weekly-v1/evaluations/runs/qfa_real_alpaca_20260626T055000Z.json`

## Command

```bash
set -a; source /Users/moonk/.hermes/profiles/alphaaoi/secrets/alpaca.env; set +a
export ALPACA_API_KEY="${ALPACA_API_KEY:-${ALPACA_KEY_ID:-}}"
export ALPACA_PAPER=true
/Users/moonk/quant-for-agent/.venv/bin/qfa backtest run \
  models/tsmom-voltarget-liquid-etf-weekly-v1/model.py \
  --symbols SPY,QQQ,IWM,TLT,GLD,SLV,USO,FXE,FXY \
  --start 2024-01-01 \
  --end 2025-12-31 \
  --db models/tsmom-voltarget-liquid-etf-weekly-v1/evaluations/qfa-real.sqlite3
```

## Model verification / adjustment

`model.py` was adjusted from fixture-friendly `min_periods: 2` to `min_periods: 127`, so the 126-day trend signal only activates once enough history exists. This avoids early-window leakage/noise from treating a few bars as medium-term momentum.

## Summary metrics

- Initial cash: `100000.0`
- Final equity: `133163.4859`
- Total return: `33.163486%`
- Annualized return: `15.528762%`
- Annualized volatility: `12.518939%`
- Sharpe: `1.21599641`
- Max drawdown: `-9.362303%`
- Win rate: `42.6%`
- Periods: `500`

## Costs / limitations

- Transaction costs/slippage: not applied. This qfa version exposes no transaction-cost, slippage, or turnover support in `backtest run` / `run_backtest`.
- Rebalance cadence: qfa calls the model daily; the model folder name says weekly, but weekly rebalancing is not currently enforceable by the qfa backtester API without engine changes.
- Random windows: not run in this pass; qfa CLI does not provide a built-in random-period protocol.
- Orthogonality: not run; no accepted/watchlist return streams found for comparison.
- Alpaca bars: qfa's `AlpacaGateway` does not expose an explicit adjusted-price flag in this repo version.

## Stale prior CSV artifacts

The old CSV fixture smoke artifacts are superseded/stale and should not be treated as alpha evidence:

- `models/tsmom-voltarget-liquid-etf-weekly-v1/evaluations/runs/qfa_smoke_20260626T012301Z.json`
- prior `models/tsmom-voltarget-liquid-etf-weekly-v1/evaluations/latest.json` / `latest.md` CSV fixture summaries overwritten by this real-data evaluation

## Suggested decision

Watchlist / continue research. The real-data window is promising pre-cost, but do **not** accept until transaction costs, turnover, random windows, and orthogonality are validated.

## Child ideas

- Refinement: `AR-003-R1` — implement scripted random-window validation plus 5 bps turnover-based cost haircut and compare 63/126/252 lookbacks with 20/60 vol windows on the same ETF universe.
- Divergent: `AR-003-D1` — test cross-sectional ETF relative-strength/defensive-rotation model using macro/liquidity proxies instead of pure time-series momentum.
