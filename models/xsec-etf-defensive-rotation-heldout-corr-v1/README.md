# xsec-etf-defensive-rotation-heldout-corr-v1 (AR-062)

Research-only QFA alpha for issue AR-062.  This is a refinement of AR-051 that keeps the same liquid ETF universe but replaces AR-051's broad proxy brake with explicit held-out correlation targets.

## Hypothesis

AR-051's robust random-window Sharpe might be retained while lowering redundancy if the rotation penalizes ETFs whose trailing returns exceed a target correlation to pre-declared held-out streams:

- TSMOM-like stream: `SPY`, `QQQ`, `IWM`, `TLT`, `GLD`.
- Carry/defensive stream: `IEF`, `TLT`, `GLD`, `XLP`, `XLU`, `SHY`.

The rule uses monthly prior-month-end decisions, blended 63/126-day momentum divided by realized volatility, an excess-correlation penalty above a 0.35 target, and a defensive sleeve floor.

## Files

- `model.py` exposes `generate_signals(context)`.
- `config.yaml` records parameters, universe, and evaluation constraints.
- `metadata.yaml` records status and artifact handles.
- `evaluations/latest.json` and `evaluations/latest.md` contain the latest real-data evaluation.
- `evaluations/runs/ar062_qfa_alpaca_real_20260626T115655Z.json` is the immutable run artifact.

## Evaluation protocol

- Data: Alpaca real daily OHLCV through qfa `AlpacaGateway` only.
- CSV: no CSV data used; `--data-csv` was not used.
- Safety: no daemon, no live trading, no orders.
- Primary window: 2023-01-01 through 2025-12-31.
- Random windows: 8 deterministic pseudo-random subwindows across 2023-2025.
- Costs: qfa native transaction costs are unavailable, so returns were post-processed with one-way turnover haircuts at 10 bps primary and 20 bps stress.

## Result

Suggested decision: **rejected**.

The held-out correlation target reduced performance too much and did not prove a lower-redundancy profile.  Primary 10 bps Sharpe was positive but weak, random-window median Sharpe was negative, and available correlation to AR-051 remained high.
