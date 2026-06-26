# Latest evaluation — AR-007 overnight-gap-reversal-megacap-v1

Status: completed Alpaca-backed qfa real-data backtest.

## Backtest setup

- Data source: Alpaca real market data via qfa backtest.
- CSV fixtures: not used; `--data-csv` omitted.
- Symbols: AAPL, MSFT, NVDA, AMZN, META, GOOGL, TSLA.
- Period: 2024-01-01 to 2025-12-31.
- Timeframe: 1Day.
- Initial cash: 100,000.
- qfa run ID: 1.
- Run JSON: `evaluations/runs/qfa_realdata_20240101_20251231_run1.json`.
- qfa SQLite DB: `evaluations/qfa_realdata.sqlite3`.

## Metrics, pre-cost/gross

- Final equity: 66,886.3330
- Total return: -33.113667%
- Annualized return: -18.347395%
- Annualized volatility: 26.868747%
- Sharpe: -0.61761503
- Max drawdown: -38.506717%
- Win rate: 23.0%
- Periods: 500

## Costs/slippage

The issue requested a 5 bps cost/slippage assumption if supported. Current qfa `backtest run` exposes no transaction-cost/slippage parameter, so costs/slippage were **not applied**. Reported metrics are pre-cost/gross.

## qfa command

```bash
set -a; source /Users/moonk/.hermes/profiles/alphaaoi/secrets/alpaca.env; set +a
export ALPACA_API_KEY="${ALPACA_API_KEY:-${ALPACA_KEY_ID:-}}"
export ALPACA_PAPER=true
/Users/moonk/quant-for-agent/.venv/bin/qfa backtest run \
  /Users/moonk/quant-for-agent/models/overnight-gap-reversal-megacap-v1/model.py \
  --symbols AAPL,MSFT,NVDA,AMZN,META,GOOGL,TSLA \
  --start 2024-01-01 --end 2025-12-31 --timeframe 1Day \
  --initial-cash 100000 \
  --db /Users/moonk/quant-for-agent/models/overnight-gap-reversal-megacap-v1/evaluations/qfa_realdata.sqlite3
```

## Interpretation

The tested qfa-compatible implementation fades large overnight gap z-scores using the latest completed daily bar and holds for the next qfa period. This is only a lagged close-to-close proxy for the intended same-day open-to-close gap reversal because the current qfa daily backtester does not simulate entry at the current session open.

Result: reject or research-watchlist only. The 2024-2025 Alpaca real-data proxy backtest produced negative Sharpe and a large drawdown before transaction costs.

## Child ideas

- Refinement child: AR-007-R1 — Test true open-to-close overnight-gap reversal with an open-aware evaluator and volatility/market-regime filters to reduce lagged proxy error and drawdown.
- Divergent child: AR-007-D1 — Mega-cap post-earnings drift continuation using earnings-calendar/event dates and multi-day holding windows rather than overnight gap fading.

## Artifact note

qfa created SQLite DB artifact `evaluations/qfa_realdata.sqlite3` under the model folder. Controller should remove it before commit if repository policy requires.
