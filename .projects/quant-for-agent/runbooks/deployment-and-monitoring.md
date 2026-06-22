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
qfa daemon run --dry-run --once
```

## Future staging/production split
- Staging: Alpaca paper account, dry-run or paper order submission, verbose logs.
- Production: Alpaca live account, explicit `--live`, stricter risk controls, persistent logs, restart policy.

## Monitoring checklist
- Daemon process health/restarts.
- Alpaca API failures.
- Trade event count and rejected orders.
- Account equity and exposure drift.
- Backtest and model registry DB backup.
