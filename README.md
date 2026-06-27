# quant-for-agent

CLI-first quant system for AI agents. MVP scope:

- Run repeatable backtests against Python alpha model modules.
- Store and query historical backtest results from SQLite.
- Register alpha models against portfolio allocations.
- Run a simple Alpaca-backed trading daemon, paper-first, with explicit `--submit-orders` required before any order placement.

## Installation

Install directly from GitHub:

```bash
python -m venv .venv
source .venv/bin/activate
pip install "git+https://github.com/knoomdevbot/quant-for-agent.git"
qfa --help
```

For development from a local checkout:

```bash
git clone https://github.com/knoomdevbot/quant-for-agent.git
cd quant-for-agent
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Quickstart from a checkout

The example alpha model and fixture CSV live in the repository, so clone the repo for the smoke test:

```bash
git clone https://github.com/knoomdevbot/quant-for-agent.git
cd quant-for-agent
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
qfa --help
qfa backtest run examples/momentum_alpha.py --symbols AAPL,MSFT --start 2024-01-01 --end 2024-03-01 --data-csv tests/fixtures/prices.csv
qfa backtest list
qfa models add examples/momentum_alpha.py --name momentum --allocation 0.25 --symbols AAPL,MSFT
qfa daemon run --once
```

`qfa daemon run` defaults to simulation/no-submit mode and prints `SIMULATION ONLY: no Alpaca orders will be submitted.` To submit to an Alpaca paper account, set `ALPACA_PAPER=true` and pass `--submit-orders`. Live brokerage submission with `ALPACA_PAPER=false` is blocked unless `--allow-live-brokerage` is also passed.

After direct `pip install "git+https://github.com/knoomdevbot/quant-for-agent.git"`, use `qfa` with your own alpha model file and data CSV paths.

## Alpha model contract

An alpha model is a Python file exposing:

```python
def generate_signals(context):
    # Return target portfolio weights by symbol. Weights are normalized by the engine.
    return {"AAPL": 0.6, "MSFT": 0.4}
```

`context` contains:

- `symbols`: list[str]
- `prices`: pandas DataFrame with columns `timestamp`, `symbol`, `open`, `high`, `low`, `close`, `volume`
- `as_of`: current timestamp
- `metadata`: dict

## Alpaca configuration

Set these environment variables for Alpaca access:

```bash
export ALPACA_API_KEY=...
export ALPACA_SECRET_KEY=...
export ALPACA_PAPER=true
```

Order placement requires passing `--submit-orders` to the daemon. With `ALPACA_PAPER=true`, orders go to the Alpaca paper account. With `ALPACA_PAPER=false`, live brokerage orders also require `--allow-live-brokerage`. Use paper trading first.
