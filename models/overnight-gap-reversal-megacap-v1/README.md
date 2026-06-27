# overnight-gap-reversal-megacap-v1

Research artifact for **AR-007 — Overnight gap reversal in mega-cap equities**.

## Hypothesis

Large overnight gaps in liquid mega-cap equities may represent short-term overreaction to news or overnight liquidity imbalance, creating partial reversal opportunities.

## Universe

AAPL, MSFT, NVDA, AMZN, META, GOOGL, TSLA.

## Model

`model.py` exposes qfa-compatible `generate_signals(context)`.

Signal logic:

- Compute overnight gap per symbol: `open_t / close_{t-1} - 1`.
- Compute prior-only 60-day rolling gap z-score.
- Fade large gaps when `abs(gap_z) >= 1.0`:
  - positive gap z-score: short
  - negative gap z-score: long
- Score by excess absolute z-score above threshold.
- Gross-normalize to 1.0 and cap absolute single-name weight at 25%.

## Important qfa limitation

The intended alpha is an open-aware overnight-gap reversal, ideally entering soon after the current day open and evaluating same-day open-to-close reversal. The current qfa daily backtest calls `generate_signals` on the latest completed daily bar and applies weights to the next close-to-close return. This implementation therefore uses the latest completed bar's open-vs-previous-close gap as a **lagged proxy**, not a true same-day open execution simulation.

## Real-data evaluation

Backtest used Alpaca real market data only; no `--data-csv` and no CSV fixtures.

Command pattern:

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

## Latest result

- Periods: 500
- Final equity: 66,886.3330
- Total return: -33.113667%
- Annualized return: -18.347395%
- Annualized volatility: 26.868747%
- Sharpe: -0.61761503
- Max drawdown: -38.506717%
- Win rate: 23.0%

Costs/slippage: requested 5 bps assumption is documented but not applied because qfa's current backtest CLI has no explicit transaction-cost/slippage parameter. Metrics are pre-cost/gross.

Decision: reject or research-watchlist only; this lagged proxy fails the positive-Sharpe acceptance threshold before costs.

## Artifacts

- `model.py`
- `config.yaml`
- `metadata.yaml`
- `evaluations/latest.json`
- `evaluations/latest.md`
- `evaluations/runs/qfa_realdata_20240101_20251231_run1.json`

SQLite note: `evaluations/qfa_realdata.sqlite3` was created by qfa under the model folder; controller should remove before commit if required by policy.
