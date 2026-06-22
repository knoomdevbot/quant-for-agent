# quant-for-agent project knowledge

## Goal
Build a CLI-first quant system that agents can use with minimal friction for two workflows:

1. Backtesting Python alpha models across multiple periods.
2. Registering active alpha models to trade a configured portfolio allocation via Alpaca.

## Product type
Developer/agent-facing CLI tool and long-running local/server daemon.

## Current status
MVP repo initialized locally at `/Users/moonk/quant-for-agent`.

## Assumptions
- Python is the best MVP language because alpha models are Python modules and pandas/numpy simplify data handling.
- SQLite is sufficient for initial durable storage of backtest results, model registry, and trade events.
- Alpaca paper trading is the default safe operating mode; live trading requires explicit opt-in.
- CLI JSON output is preferred so other agents can parse results.

## Open questions
- Should live deployment run on the user's machine, VPS, or managed container host?
- Should portfolio construction support net exposure/leverage/risk limits beyond sleeve allocation in the first release?
- Which market/data universe should be supported first: US equities only, crypto, or both?
