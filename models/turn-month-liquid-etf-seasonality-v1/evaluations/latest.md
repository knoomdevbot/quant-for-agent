# AR-006 latest evaluation — turn-month-liquid-etf-seasonality-v1

## Summary
- Evaluation: real-data qfa Alpaca backtest
- Data source: Alpaca real market data via qfa AlpacaGateway; `--data-csv` was not used
- Window: 2024-01-01 to 2025-12-31, timeframe 1Day
- Universe: SPY, QQQ, IWM, TLT, GLD
- Strategy: long-only equal weight during final 3 business days and first 3 business days of each month; flat otherwise
- Costs/slippage: not applied; qfa in this repo version has no explicit transaction-cost/slippage support
- Trading/daemon: no trades placed; qfa daemon not run

## Metrics
- Final equity: 102693.3164
- Total return: 0.02693316
- Annualized return: 0.01348484
- Annualized volatility: 0.06371129
- Sharpe: 0.24228949
- Max drawdown: -0.09795005
- Win rate: 0.144
- Periods: 500

## Command
```bash
set -a; source /Users/moonk/.hermes/profiles/alphaaoi/secrets/alpaca.env; set +a; export ALPACA_API_KEY="${ALPACA_API_KEY:-${ALPACA_KEY_ID:-}}"; export ALPACA_PAPER=true; /Users/moonk/quant-for-agent/.venv/bin/python -m py_compile models/turn-month-liquid-etf-seasonality-v1/model.py && /Users/moonk/quant-for-agent/.venv/bin/qfa backtest run models/turn-month-liquid-etf-seasonality-v1/model.py --symbols SPY,QQQ,IWM,TLT,GLD --start 2024-01-01 --end 2025-12-31 --db models/turn-month-liquid-etf-seasonality-v1/evaluations/qfa-real.sqlite3
```

## Artifacts
- Run JSON: `models/turn-month-liquid-etf-seasonality-v1/evaluations/runs/qfa_real_alpaca_20260626T062022Z.json`
- Latest JSON: `models/turn-month-liquid-etf-seasonality-v1/evaluations/latest.json`
- qfa SQLite DB artifact: `models/turn-month-liquid-etf-seasonality-v1/evaluations/qfa-real.sqlite3` (runtime artifact noted for controller cleanup before commit)

## Decision
Suggested decision: `watchlist_continue_research_not_accept_until_costed_random_window_validation`.

## Child ideas
- Refinement child: AR-006-R1: add exchange-calendar-aware turn-of-month window search with turnover-based 5 bps cost haircut and 30 random-window robustness validation.
- Divergent child: AR-006-D1: test non-calendar ETF flow signals using cross-asset risk-on/risk-off breadth and volatility regime features rather than month-boundary timing.
