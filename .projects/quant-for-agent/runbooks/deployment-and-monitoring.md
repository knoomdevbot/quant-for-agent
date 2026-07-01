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

Enable daemon email notifications with one SMTP URL plus recipients. Notifications are best-effort and never crash the trading loop. The daemon sends email on observed market open/close transitions and when a tick records actionable buy/sell position-change events; in simulation mode, position-change emails describe preview trade events.

```bash
qfa daemon run --interval-seconds 300 \
  --notify-email-to ops@example.com \
  --notify-email-smtp-url 'smtps://qfa%40example.com:APP_PASSWORD@smtp.example.com?from=qfa@example.com'
```

For service supervisors, put the SMTP URL in a single environment variable instead of passing it on the command line:

```bash
export QFA_NOTIFY_EMAIL_TO=ops@example.com
export QFA_NOTIFY_EMAIL_SMTP_URL='smtps://qfa%40example.com:APP_PASSWORD@smtp.example.com?from=qfa@example.com'
qfa daemon run --interval-seconds 300
```

The older split SMTP env vars (`QFA_SMTP_HOST`, `QFA_SMTP_PORT`, `QFA_NOTIFY_EMAIL_FROM`, `QFA_SMTP_USERNAME`, `QFA_SMTP_PASSWORD`, `QFA_SMTP_TLS`) still work for deployments that prefer separate secret fields.

Use the orphan-position guard when the broker account may contain positions outside the active qfa model universe:

```bash
# Report unmanaged positions without submitting orders.
qfa daemon run --once --orphan-position-mode report --orphan-min-notional 25

# Preview paper liquidation orders in simulation/no-submit mode.
qfa daemon run --once --orphan-position-mode liquidate --orphan-min-notional 25

# Submit orphan-position liquidation orders only to Alpaca paper.
ALPACA_PAPER=true qfa daemon run --submit-orders --orphan-position-mode liquidate --orphan-min-notional 25
```

`--orphan-position-mode liquidate` is blocked for live brokerage even when `--allow-live-brokerage` is present. Orphan guard events are recorded in `trade_events` with `model_name=__orphan_position_guard__`; existing open orders on an orphan symbol cause the guard to skip that symbol instead of submitting another order.

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
