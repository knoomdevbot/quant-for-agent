# meanrev-zscore-liquid-etf-1d-v1

AR-002 seed alpha: short-term mean reversion after stretched 3-day moves in liquid ETFs.

## Hypothesis

Highly liquid ETFs that move unusually far over a short 3-day horizon may partially revert over the next trading day as temporary order-flow pressure is absorbed.

## Model

`model.py` exposes the qfa contract:

```python
def generate_signals(context):
    return {"SPY": weight, ...}
```

Signal logic:

- Pivot close prices by symbol using only qfa-provided history through `context.as_of`.
- Compute each symbol's latest trailing 3-day close-to-close return.
- Z-score that latest 3-day return against a trailing 20-observation sample of 3-day returns.
- If `abs(z) >= entry_z`, take the opposite sign (`-z`) for one-day mean reversion.
- Normalize active signals to gross exposure 1.0; cap concentration before final normalization.

Primary research parameters:

- Universe: `SPY, QQQ, IWM, TLT, GLD, SLV, XLF, XLK, XLE, XLV`
- `return_lookback_days`: 3
- `z_window`: 20, with search candidate 60
- `entry_z`: 1.0, with search candidates 1.5 and 2.0
- Exit horizon: one day via qfa daily re-evaluation

## Latest real-data evaluation

- latest JSON: `evaluations/latest.json`
- latest summary: `evaluations/latest.md`
- run JSON: `evaluations/runs/qfa_realdata_20260626T054638Z.json`
- qfa DB: `evaluations/qfa_realdata.sqlite3`
- stale CSV note: `evaluations/STALE_CSV_RESULTS.md`

Command used omitted `--data-csv` and pulled Alpaca market data through qfa. No daemon was run and no trades/orders were placed.

Metrics for `2024-01-01` to `2025-12-31` on `SPY,QQQ,IWM,TLT,GLD,SLV,XLF,XLK,XLE,XLV`:

- periods: `500`
- final equity: `79763.4397`
- total return: `-0.2023656`
- annualized return: `-0.10770358`
- annualized volatility: `0.14567079`
- Sharpe: `-0.70937156`
- max drawdown: `-0.35148562`
- win rate: `0.434`

## Evaluation limitations

- qfa currently exposes no transaction-cost/slippage parameter in `backtest run`; the requested 5 bps cost assumption is documented but not applied.
- Metrics are therefore gross of costs and would likely deteriorate after costs.
- Only one contiguous real-data window was run; random-window robustness remains a follow-up.
- Previous local CSV fixture smoke artifacts are stale and should not be used for model selection.

## Suggested decision

Reject for acceptance in current form. Keep as a research seed/watchlist item only if a refinement branch is pursued; the real-data ETF result is negative before costs.

## Child ideas

- Refinement child: `AR-002-R1` — add regime/volatility filters, volatility-scaled sizing, parameter sweep `z_window=[20,60]`, `entry_z=[1.0,1.5,2.0]`, and explicit turnover/cost modeling before reconsideration.
- Divergent child: `AR-002-D1` — test ETF overnight gap reversal or intraday open-to-close reversal using a different return driver/horizon instead of 3-day close-to-close z-score.
