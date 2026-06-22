# MVP Technical Spec — quant-for-agent

## Current architecture summary
New Python package with Typer CLI, pandas/numpy backtesting engine, SQLite persistence, and Alpaca integration via `alpaca-py`.

## Components
- `quant_for_agent.cli`: Typer CLI entrypoint `qfa`.
- `quant_for_agent.alpha`: Python alpha model loader and signal normalization.
- `quant_for_agent.backtest`: daily close-to-close backtest engine and metrics.
- `quant_for_agent.storage`: SQLite schema and repository methods.
- `quant_for_agent.data`: local CSV OHLCV loader.
- `quant_for_agent.alpaca_client`: Alpaca market data and trading gateway.
- `quant_for_agent.daemon`: simple long-running trading loop.

## Interfaces
### Alpha model
```python
def generate_signals(context: AlphaContext) -> dict[str, float]
```
Returned values are target weights within the model sleeve. Weights are gross-normalized by the engine.

### CLI
- `qfa backtest run MODEL --symbols AAPL,MSFT --start YYYY-MM-DD --end YYYY-MM-DD [--data-csv path]`
- `qfa backtest list [--limit N]`
- `qfa backtest show RUN_ID`
- `qfa models add MODEL --name NAME --allocation FLOAT --symbols AAPL,MSFT`
- `qfa models update NAME MODEL --allocation FLOAT --symbols AAPL,MSFT`
- `qfa models remove NAME`
- `qfa models list`
- `qfa daemon run [--dry-run/--no-dry-run] [--live] [--once]`

## Persistence schema
SQLite tables:
- `backtest_runs`: run params, metrics JSON, equity curve JSON.
- `alpha_models`: model registry with allocation and symbols.
- `trade_events`: dry-run/live order audit trail.

## Data flow
### Backtest
CLI → load CSV or Alpaca bars → load alpha model → iterate timestamps → compute normalized weights → apply next-period returns → calculate metrics → persist run → emit JSON.

### Trading daemon
CLI → load active models → get Alpaca account equity/recent bars → call each alpha model → normalize weights inside allocation sleeve → submit notional orders or dry-run events → persist events.

## Error handling
- Missing alpha file/callback fails fast with clear exception.
- Missing Alpaca env vars fail before network calls.
- Missing/invalid CSV columns fail before backtesting.
- Empty price range or too few bars fails with actionable message.

## Security / privacy / financial safety
- No credentials in repo; env vars only.
- Paper/dry-run first.
- Live order placement requires `--live` and `--no-dry-run` behavior can be added later; current effective dry-run remains true unless `--live` is passed.
- MVP order sizing is simple notional market orders; production use needs risk controls and reconciliation.

## Hosting / deployment recommendation
This stack needs a long-running process, filesystem or mounted-volume SQLite, env secrets, logs, and scheduled restart. Recommended MVP host: a small VPS or Fly.io/Render worker. For earliest validation, run locally or on a cheap VPS because Alpaca credentials and daemon logs are easy to inspect. Add systemd/Docker runbook before production live trading.

## Tests
- Unit tests for backtest metrics and result persistence.
- Unit tests for model registry CRUD.
- Future: mocked Alpaca daemon tick test, CLI invocation tests, risk-limit tests.
