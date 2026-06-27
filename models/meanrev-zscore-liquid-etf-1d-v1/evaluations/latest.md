# AR-002 evaluation: meanrev-zscore-liquid-etf-1d-v1

## Run handle

- qfa run id: `1`
- qfa DB: `models/meanrev-zscore-liquid-etf-1d-v1/evaluations/qfa_realdata.sqlite3`
- latest JSON: `models/meanrev-zscore-liquid-etf-1d-v1/evaluations/latest.json`
- run JSON: `models/meanrev-zscore-liquid-etf-1d-v1/evaluations/runs/qfa_realdata_20260626T054638Z.json`
- stale CSV note: `models/meanrev-zscore-liquid-etf-1d-v1/evaluations/STALE_CSV_RESULTS.md`

## Command run

```bash
set -a; source /Users/moonk/.hermes/profiles/alphaaoi/secrets/alpaca.env; set +a
export ALPACA_API_KEY="${ALPACA_API_KEY:-${ALPACA_KEY_ID:-}}"
export ALPACA_PAPER=true
/Users/moonk/quant-for-agent/.venv/bin/qfa backtest run \
  models/meanrev-zscore-liquid-etf-1d-v1/model.py \
  --symbols SPY,QQQ,IWM,TLT,GLD,SLV,XLF,XLK,XLE,XLV \
  --start 2024-01-01 \
  --end 2025-12-31 \
  --timeframe 1Day \
  --initial-cash 100000 \
  --db models/meanrev-zscore-liquid-etf-1d-v1/evaluations/qfa_realdata.sqlite3
```

No `--data-csv` was used. No daemon was run. No trades/orders were placed.

## Real-data metrics (gross of costs)

- data source: Alpaca market data via qfa AlpacaGateway
- symbols: `SPY,QQQ,IWM,TLT,GLD,SLV,XLF,XLK,XLE,XLV`
- requested start: `2024-01-01`
- requested end: `2025-12-31`
- first equity timestamp: `2024-01-03T05:00:00+00:00`
- last equity timestamp: `2025-12-30T05:00:00+00:00`
- periods: `500`
- initial cash: `100000.0`
- final equity: `79763.4397`
- total return: `-0.2023656`
- annualized return: `-0.10770358`
- annualized volatility: `0.14567079`
- Sharpe: `-0.70937156`
- max drawdown: `-0.35148562`
- win rate: `0.434`

## Signal evaluated

- AR-002-aligned short-term ETF mean reversion.
- For each ETF, compute trailing 3-day close-to-close return.
- Z-score latest 3-day return against trailing 20 observed 3-day returns.
- If `abs(z) >= 1.0`, take the opposite sign for next-day mean reversion.
- Gross-normalize active legs with a pre-normalization absolute-weight cap.

## Warnings and limitations

- qfa `backtest run` exposes no transaction-cost/slippage parameter, so the requested 5 bps cost assumption is documented but **not applied**; metrics are gross of costs.
- This is one contiguous real-data window, not the full 30 random-window protocol.
- Alpaca/qfa returned 500 portfolio periods with the final equity point on `2025-12-30`, despite requested end `2025-12-31`.
- The result is negative before costs; after costs it would be worse.
- Old fixture/CSV smoke outputs in this folder are stale and should not be used for model selection.

## Suggested decision

Reject for acceptance in current form; keep only as a research seed/watchlist item if further refinement is desired. The real-data ETF test fails the AR-002 falsifier direction with negative Sharpe and large drawdown before costs.

## Child ideas

- Refinement child: `AR-002-R1` — add regime/volatility filters, volatility-scaled sizing, parameter sweep `z_window=[20,60]`, `entry_z=[1.0,1.5,2.0]`, and explicit turnover/cost modeling before reconsideration.
- Divergent child: `AR-002-D1` — test ETF overnight gap reversal or intraday open-to-close reversal using a different return driver/horizon instead of 3-day close-to-close z-score.
