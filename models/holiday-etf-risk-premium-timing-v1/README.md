# holiday-etf-risk-premium-timing-v1

AR-127 researches whether public NYSE holiday closures create short-horizon ETF risk-premium timing effects distinct from turn-of-month, OPEX, payday, and month-end controls.

## Model

`model.py` exposes `generate_signals(context)` for qfa. It is deterministic and uses only public calendar rules embedded in code:

- if the next qfa daily holding interval is the last session before a full-day NYSE closure, hold an equal-weight risk-on ETF basket;
- if the next interval is the first session after a full-day NYSE closure, hold an equal-weight defensive basket as a diagnostic;
- otherwise hold cash.

Primary research support is for the pre-holiday risk-on leg only. The post-holiday defensive leg was negative in evaluation and should not be advanced without rework.

## Universe and filters

Candidate ETFs span equity beta, sectors, credit, duration, commodities/gold/energy, and defensive/cash/FX. Selection used only Alpaca/qfa daily OHLCV coverage and liquidity proxy filters, not returns.

## Evaluation

See:

- `evaluations/latest.json`
- `evaluations/latest.md`
- `evaluations/runs/ar127_20260627T143602Z.json`

Guardrail booleans in the JSON root: `no_csv_used=true`, `no_data_csv_argument_used=true`, `no_daemon=true`, `no_orders=true`, `raw_daily_paths_retained=false`.

No raw bars, daily returns, equity curves, or weight tails are retained in the artifacts.
