# Core PRD — quant-for-agent

## Value proposition
A CLI-first quant toolkit that lets AI agents safely backtest Python alpha models, persist results, and operate simple Alpaca paper/live trading workflows without bespoke glue code.

## Primary critical user journey
An agent writes or receives a Python alpha model, runs a backtest over a requested symbol/date range, queries stored metrics, registers the model with a portfolio allocation, and starts a paper-trading daemon connected to Alpaca.

## Target users
- AI agents building/researching trading strategies.
- Developers who want automation-friendly backtesting/trading primitives.
- Quant hobbyists using Alpaca paper trading.

## Non-goals for MVP
- Institutional-grade execution algorithms.
- Multi-broker support.
- Advanced portfolio optimization, leverage, margin, tax lots, or compliance workflow.
- Web UI.
- Guaranteed profitable strategies.

## MVP behavior
### Backtesting
- Accept alpha models as Python files exposing `generate_signals(context)`.
- Support local CSV price data and Alpaca historical bars.
- Run a simple daily close-to-close backtest over one or more symbols.
- Calculate metrics: final equity, total return, annualized return, annualized volatility, Sharpe, max drawdown, win rate, period count.
- Persist every backtest run and equity curve to SQLite.
- Provide CLI commands to list/show previous backtests as JSON.

### Trading
- Add/update/remove/list alpha models in a local model registry.
- Each model has name, file path, allocation, symbols, and active state.
- Daemon loads active models, requests recent Alpaca bars, computes target signals, and submits notional market orders.
- Default mode is dry-run/paper-safe; live order placement requires explicit `--live`.
- Store trade events for auditability.

## Success metrics
- An agent can run the README quickstart without reading source code.
- Backtest results are machine-readable JSON and persisted.
- Trading daemon can execute one dry-run tick with registered models.
- No secrets are committed; Alpaca credentials come from env vars.

## Launch constraints / safety
- Financial-risk disclaimer in docs before public release.
- Paper trading must remain the default.
- Live trading must require explicit CLI opt-in and documented env setup.
- MVP should be deterministic enough for tests using fixture data.

## Feedback path
- Initial feedback channel: this Telegram thread and future GitHub issues once remote repo exists.
- Feedback log: `.projects/quant-for-agent/feedback/daily-log.md`.
- Owner: NED during active development.

## Daily feedback review
During active development/beta, check Telegram/client feedback and GitHub issues daily. Record themes, bugs, product opportunities, no-action items, and decisions in `.projects/quant-for-agent/feedback/daily-log.md`.

## Acceptance criteria
- `qfa backtest run` accepts a Python alpha model and returns JSON with `metrics.sharpe`.
- `qfa backtest list/show` can retrieve stored results.
- `qfa models add/update/remove/list` manages model allocation registry.
- `qfa daemon run --dry-run --once` can process active models without placing orders.
- Unit tests cover metrics/storage and model registry.
