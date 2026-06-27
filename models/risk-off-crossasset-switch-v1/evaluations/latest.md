# AR-008 real-data evaluation: risk-off-crossasset-switch-v1

- Status: completed real-data qfa backtest
- Created: 2026-06-26T06:28:32Z
- Data source: Alpaca market data via qfa backtest; `--data-csv` was not used
- Run JSON: `evaluations/runs/qfa_realdata_20240101_20251231_run1.json`
- QFA DB: `evaluations/qfa_realdata.sqlite`

## Command

```bash
set -a; source /Users/moonk/.hermes/profiles/alphaaoi/secrets/alpaca.env; set +a; export ALPACA_API_KEY="${ALPACA_API_KEY:-${ALPACA_KEY_ID:-}}"; export ALPACA_PAPER=true; /Users/moonk/quant-for-agent/.venv/bin/qfa backtest run /Users/moonk/quant-for-agent/models/risk-off-crossasset-switch-v1/model.py --symbols SPY,QQQ,IWM,TLT,GLD,XLU,XLE --start 2024-01-01 --end 2025-12-31 --timeframe 1Day --initial-cash 100000 --db /Users/moonk/quant-for-agent/models/risk-off-crossasset-switch-v1/evaluations/qfa_realdata.sqlite
```

## Setup / model review

Implemented `model.py` for AR-008 as a qfa-compatible rule-based `generate_signals(context)` model. It uses only OHLCV close data from qfa context over SPY, QQQ, IWM, TLT, GLD, XLU, and XLE. The switch uses 60-day equity trend/breadth, 20-day SPY realized volatility, and 20-day TLT/GLD relative strength versus SPY. Risk-on allocates to SPY/QQQ/IWM/XLE; risk-off allocates to TLT/GLD/XLU. Weights are long-only, gross-normalized, and capped at 0.45 absolute weight.

## Metrics, pre-cost

- Period: 2024-01-01 to 2025-12-31
- Symbols: SPY, QQQ, IWM, TLT, GLD, XLU, XLE
- QFA run id: 1
- Equity points / periods: 500 / 500
- Initial cash: 100000.00
- Final equity: 125110.0083
- Total return: 0.25110008
- Annualized return: 0.11952860
- Annualized volatility: 0.15982935
- Sharpe: 0.78756489
- Max drawdown: -0.18723612
- Win rate: 0.48800000

## Costs / caveats

- Intended cost assumption from AR-008: 5 bps.
- Current qfa backtest CLI has no transaction-cost/slippage parameter, so costs were **not applied**.
- Metrics are therefore pre-cost and likely optimistic versus executable performance.
- No trades were placed and the qfa daemon was not run.
- Alpaca real market data was used; no CSV fixture or `--data-csv` was used.

## Suggested decision

Watchlist/refine rather than accept outright. The single full-window real-data result is positive before costs (Sharpe 0.7876, total return 25.11%, max drawdown -18.72%), but transaction costs/slippage were not applied and random-window robustness was not completed.

## Child ideas

- Refinement child: AR-008-R1 parameter-stability and turnover-aware cost study for equity_lookback=[40,60,100], stress_lookback=[10,20,40], defensive_stress_threshold=[0.02,0.04,0.06] on Alpaca data.
- Divergent child: AR-008-D1 intraday index-futures or ETF gap-reversal risk-off detector using open-to-close behavior after overnight stress instead of daily close-to-close allocation.
