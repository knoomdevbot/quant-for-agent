# crosssec-momentum-liquid-megacap-daily-v1

Research artifact for `alpha_research/issues/AR-001.md`.

## Hypothesis

Liquid mega-cap stocks with stronger intermediate 3-6 month returns, skipping the most recent week, may continue outperforming over a 5-day horizon because information and institutional flows diffuse slowly.

## Implementation

- QFA contract: `model.py` exposes `generate_signals(context)`.
- Universe: `AAPL, MSFT, NVDA, AMZN, META, GOOGL, TSLA`.
- Signal: 63-trading-day return ending 5 sessions before `as_of`.
- Optional adjustment: divide by recent 20-day realized volatility.
- Sizing: demean cross-sectional scores, gross-normalize to 1.0, cap single-name absolute weight at 0.25.
- Safety: this artifact never places trades and was evaluated only with `qfa backtest run`; daemon was not run.

## Latest evaluation

Real-data Alpaca-backed qfa backtest completed 2026-06-26. Previous fixture/CSV smoke results are stale.

- Period: 2024-01-01 to 2025-12-31
- Data: Alpaca market data, no `--data-csv`
- Run JSON: `evaluations/runs/qfa_realdata_20240101_20251231_run1.json`
- Latest JSON: `evaluations/latest.json`
- Latest Markdown: `evaluations/latest.md`
- QFA DB: `evaluations/qfa_realdata.sqlite`

Key pre-cost metrics:

- Sharpe: -0.99519064
- Total return: -0.30712541
- Annualized return: -0.16882985
- Annualized volatility: 0.17069684
- Max drawdown: -0.36715277
- Win rate: 0.41000000
- Final equity: 69287.4594

Costs were not applied because the current qfa backtest CLI does not expose transaction-cost/slippage controls.

## Decision

Suggested decision: **reject for alpha-library acceptance or trading**. The real-data result is negative before costs and has a large drawdown.

## Child ideas

- Refinement: AR-001-R1 invert/test anti-momentum variant or add regime/cost/turnover filters and parameter stability sweep.
- Divergent: AR-001-D1 mega-cap post-earnings announcement drift / analyst-revision event signal.
