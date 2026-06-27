# nyse-holiday-preclose-etf-drift-v1

AR-127 qfa-compatible research artifact for NYSE holiday pre-close equity ETF drift and post-holiday normalization.

## Signal

- Fixed broad equity basket: SPY, QQQ, IWM, DIA.
- Deterministic public calendar only: modern NYSE full-close holidays plus regular early closes (day after Thanksgiving, Christmas Eve when a trading day, July 3 when applicable).
- Separate event sleeves evaluated: last session before a full holiday, deterministic early-close session, and first session after a full holiday.
- `generate_signals(context)` uses qfa/Alpaca OHLCV only for history/tradability checks; no orders, no daemon, no CSV.

## Evaluation summary

Real Alpaca/qfa daily OHLCV, 2020-01-02 through 2026-06-25, broad ETF/sector/control pool. Compact artifacts retain no raw bars, no equity curves, no weight tails, and no SQLite DB/cache.

Decision: **rejected**.

Key metrics at 10 bps one-way cost (round trip charged per event):

- Combined event count: `124`.
- Primary combined Sharpe: `-3.19189849`.
- Primary hit rate: `0.44354839`.
- Random-window median Sharpe: `-5.27638303`.
- Random-window p25 Sharpe: `-6.204387`.
- Worst random-window Sharpe: `-7.67519395`.
- Positive-window rate: `0.0`.
- Random-label placebo percentile: `0.14`.
- Matched same-weekday placebo Sharpe: `-1.82465301`.

Rejection rationale: the effect failed random-window robustness, had materially negative p25/worst-window Sharpe, zero positive-window rate, and did not beat placebo labels.

## Artifacts

- `model.py`
- `config.yaml`
- `metadata.yaml`
- `evaluations/latest.json`
- `evaluations/latest.md`
- `evaluations/runs/ar127_qfa_alpaca_real_20260627T221353Z.json`
