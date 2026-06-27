# turn-month-liquid-etf-seasonality-v1

AR-006 research model: broad liquid ETF turn-of-month seasonality.

## Hypothesis
Month-end and beginning-of-month institutional flows may create predictable short-horizon return patterns in broad ETFs.

## Model
- QFA entry point: `generate_signals(context)` in `model.py`.
- Universe: SPY, QQQ, IWM, TLT, GLD.
- Signal: long-only equal-weight basket during the final 3 business days and first 3 business days of each calendar month; flat otherwise.
- Risk: model caps single-name pre-engine weight at 25%; qfa then normalizes gross exposure.

## Latest real-data evaluation
- Command used Alpaca real market data via qfa AlpacaGateway; `--data-csv` was omitted.
- Backtest window: 2024-01-01 to 2025-12-31, timeframe 1Day.
- Costs/slippage: not applied because this qfa version has no explicit cost/slippage support.
- No trades were placed; qfa daemon was not run.

Metrics from `evaluations/latest.json`:
- Total return: 0.02693316
- Annualized return: 0.01348484
- Annualized volatility: 0.06371129
- Sharpe: 0.24228949
- Max drawdown: -0.09795005
- Win rate: 0.144
- Periods: 500

## Artifacts
- `model.py`
- `config.yaml`
- `metadata.yaml`
- `evaluations/latest.json`
- `evaluations/latest.md`
- `evaluations/runs/qfa_real_alpaca_20260626T062022Z.json`
- Runtime DB artifact noted: `evaluations/qfa-real.sqlite3`

## Suggested decision
Watchlist / continue research; do not accept until costed random-window validation is complete.

## Child ideas
- Refinement child: AR-006-R1: add exchange-calendar-aware turn-of-month window search with turnover-based 5 bps cost haircut and 30 random-window robustness validation.
- Divergent child: AR-006-D1: test non-calendar ETF flow signals using cross-asset risk-on/risk-off breadth and volatility regime features rather than month-boundary timing.
