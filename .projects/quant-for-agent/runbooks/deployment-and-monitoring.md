# Deployment and Monitoring Runbook — quant-for-agent

## Current state
MVP is local-only. Do not run live trading until Milestone 3 risk controls and ops checks are complete.

## Required secrets
- `ALPACA_API_KEY`
- `ALPACA_SECRET_KEY`
- `ALPACA_PAPER=true` for paper/staging

## Local operation
```bash
source .venv/bin/activate
qfa models list
qfa daemon run --once
qfa daemon status --max-age-seconds 900
```

`qfa daemon run` defaults to simulation/no-submit mode. Paper order submission requires the explicit `--submit-orders` opt-in with `ALPACA_PAPER=true`; live brokerage remains out of scope for the MVP.

## Future staging/production split
- Staging: Alpaca paper account, simulation/no-submit or explicit paper order submission, verbose logs.
- Production: Alpaca live account, explicit submit/live interlocks, stricter risk controls, persistent logs, restart policy.

## Supervisor health guidance
Use `qfa daemon status --max-age-seconds <threshold>` as the canonical restart healthcheck. It exits nonzero only when no heartbeat exists, the heartbeat is stale, or the last recorded tick status is `error`.

Do **not** infer daemon failure from the absence or age of `trade_events`: a healthy tick can legitimately submit no orders when there are no active models, no signals, market-closed skips, or no rebalance delta. Instead, rely on the heartbeat row and the daemon's per-tick JSON log lines (`event=daemon_tick`) which include tick start/end timestamps, status, simulation vs submit mode, next scheduled tick, trade-event count, no-order reason, and sanitized error details when applicable.

## Monitoring checklist
- Daemon process health/restarts.
- `qfa daemon status --max-age-seconds <threshold>` result and heartbeat age.
- Per-tick `daemon_tick` logs, including no-op ticks and sanitized errors.
- Alpaca API failures.
- Trade event count and rejected orders as trading activity signals, not daemon liveness.
- Account equity and exposure drift.
- Backtest and model registry DB backup.
