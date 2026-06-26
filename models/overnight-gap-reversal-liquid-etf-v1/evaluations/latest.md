# AR-012 latest evaluation — overnight-gap-reversal-liquid-etf-v1

## Decision

**REJECTED** — Accepted only if median random-window cost-adjusted Sharpe and full-sample 5 bps Sharpe are positive with enough events; otherwise rejected/watchlist.

The selected open-to-close specification did **not** meet the acceptance threshold after the simple 5 bps-per-side cost/slippage model: median random-window Sharpe was -0.374274, and full-sample 5 bps Sharpe was -0.812568.

## Data source and command handles

- Provider: Alpaca real market data via `quant_for_agent.alpaca_client.AlpacaGateway.get_bars`.
- CSV fixtures: **not used**; no `--data-csv`.
- Trades: **none placed**; `ALPACA_PAPER=true` was set.
- Date range: 2021-01-01 to 2026-06-24.
- Universe: SPY, QQQ, IWM, TLT, GLD, SLV, XLF, XLK, XLE, XLV.
- Bar counts: {'GLD': 1373, 'IWM': 1373, 'QQQ': 1373, 'SLV': 1373, 'SPY': 1373, 'TLT': 1373, 'XLE': 1373, 'XLF': 1373, 'XLK': 1373, 'XLV': 1373}.

Credential setup command used without printing values:

```bash
set -a; source /Users/moonk/.hermes/profiles/alphaaoi/secrets/alpaca.env; set +a
export ALPACA_API_KEY="${ALPACA_API_KEY:-${ALPACA_KEY_ID:-}}"
export ALPACA_PAPER=true
```

Research harness command:

```bash
PYTHONPATH=/Users/moonk/quant-for-agent/src /Users/moonk/quant-for-agent/.venv/bin/python /tmp/evaluate_ar012.py
```

qfa real-data smoke command:

```bash
PYTHONPATH=/Users/moonk/quant-for-agent/src qfa backtest run models/overnight-gap-reversal-liquid-etf-v1/model.py --symbols SPY,QQQ,IWM,TLT,GLD,SLV,XLF,XLK,XLE,XLV --start 2024-01-01 --end 2025-12-31 --timeframe 1Day --initial-cash 100000 --db /tmp/ar012-qfa-<mktemp>.sqlite3
```

SQLite DB used by qfa smoke: `/tmp/ar012-qfa-<mktemp>.sqlite3`. It was created during execution and removed after extracting compact metrics; `db_artifact_retained=false` and no SQLite DB is retained in model artifacts.

## Selected model parameters

- gap z-window: 60
- entry z: 1.5
- market filter: True (skip days when SPY itself has a large normalized gap)
- max absolute ETF weight: 25%
- gross exposure target on event days: 1.0

## Full-sample intended open-to-close metrics, 5 bps per side

- Periods: 1312
- Event days: 461
- Instrument events: 746
- Final equity: $61,284.91
- Total return: -38.72%
- Annualized return: -8.98%
- Annualized volatility: 10.84%
- Sharpe: -0.812568
- Max drawdown: -43.43%
- Win rate: 15.55%
- Average daily turnover proxy: 0.702744

## Random-window protocol

- 30 random windows, 126 trading days each, seed 12012.
- Median 5 bps-cost Sharpe: -0.374274
- Median annualized return: -4.11%
- Median max drawdown: -7.73%
- Median event days/window: 43.000000
- Median instrument events/window: 66.000000

## qfa CLI real-data smoke metrics (lagged proxy only)

qfa loaded the same `model.py` and Alpaca daily data successfully. Because qfa daily backtests are close-to-close, these metrics are **not** the intended open-to-close research result.

- qfa run id: 1
- Periods: 500
- Total return: 17.15%
- Annualized return: 8.30%
- Sharpe: 0.826294
- Max drawdown: -9.97%

## Costs/slippage caveat

qfa's current CLI has no explicit transaction-cost/slippage parameter, so the qfa smoke metrics are gross/pre-cost. The direct research harness applied a simple ETF open-to-close model: cost = `2 * per_side_bps * gross / 10000` on event days, with sensitivity stored in `latest.json` for 0, 5, 10, and 20 bps per side. Real open executions may be worse than daily OHLC bars imply.

## Orthogonality

UNAVAILABLE: No retained parent AR-002 return stream or common factor library was available in the repo artifacts for correlation/orthogonality measurement; qualitatively different from AR-002 by horizon (overnight/intraday) and universe (liquid ETFs).

## Child idea

Because AR-012 was rejected, no refinement/extension of the failed gap-reversal hypothesis is proposed.

- Divergent: **AR-035 — Cross-asset ETF volatility-risk rotation**. Instead of extending the rejected reversal mechanism, test whether large ETF overnight gaps continue when cross-asset risk indicators align, targeting macro-news trend continuation rather than opening-imbalance reversal.
