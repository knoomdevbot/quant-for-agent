# MVP Milestone Plan — quant-for-agent

## Milestone 1 — CLI backtesting works end-to-end
Goal: A user/agent can run a Python alpha model over fixture or Alpaca data, receive metrics including Sharpe, and query persisted results.

Tasks:
- Define alpha model contract and example model.
- Implement data loader and backtest engine.
- Implement SQLite backtest persistence.
- Implement `qfa backtest run/list/show`.
- Add tests for metrics and persistence.

Acceptance evidence:
- `pytest` passes.
- `qfa backtest run examples/momentum_alpha.py ... --data-csv tests/fixtures/prices.csv` returns JSON containing `metrics.sharpe` and `id`.

## Milestone 2 — Trading registry and dry-run daemon
Goal: A user/agent can register models with allocations and run a single dry-run daemon tick without placing orders.

Tasks:
- Implement alpha model registry commands.
- Implement Alpaca gateway wrapper.
- Implement daemon loop and trade event storage.
- Add dry-run-by-default safety behavior.
- Add tests for registry CRUD; add mocked daemon tests next.

Acceptance evidence:
- `qfa models add/list/remove` works against a temp DB.
- `qfa daemon run --dry-run --once` is available and documented.

## Milestone 3 — Operational readiness before live trading
Goal: The daemon can be run safely on a persistent host with documented secrets, logs, restart, and rollback.

Tasks:
- Add Dockerfile or systemd runbook.
- Add CI for lint/tests.
- Add mocked Alpaca integration tests.
- Add risk controls: allocation cap, max order notional, market-hours guard, account/equity reconciliation.
- Add deployment and monitoring runbook.

Acceptance evidence:
- CI passes on PR.
- Runbook documents staging/paper and production/live separation.
- Live trading remains blocked unless explicit safety config is present.
