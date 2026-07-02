# quant-for-agent

CLI-first quant system for AI agents. MVP scope:

- Run repeatable backtests against Python alpha model modules.
- Store and query historical backtest results from SQLite.
- Register alpha models against portfolio allocations.
- Read/write custom time-series features for alpha research.
- Discover local factor repositories, run Python factor calculators, and persist computed factor observations.
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

## Config file

qfa can read defaults from a TOML config file so agents do not need to pass every setting as an env var.

Default path:

```bash
~/.qfa/config.toml
```

Override path:

```bash
qfa --config ./qfa.toml config show
QFA_CONFIG=./qfa.toml qfa config show
```

Precedence is:

```text
CLI option > environment variable > config file > built-in default
```

Example:

```toml
[core]
db = "~/.qfa/qfa.sqlite3"
health_log = "~/.qfa/daemon-health.jsonl"

[factor_store]
backend = "sqlite" # sqlite | dynamodb
table = "qfa-feature-observations" # existing compatibility default
region = "us-west-2"

[factor_repository]
repository_paths = ["./factors", "~/.qfa/factors"]
max_staleness_seconds = 86400

[alpaca]
paper = true
data_feed = "iex"
```

Inspect resolved config with secrets redacted:

```bash
qfa config show
```

## Factor Store

qfa supports custom time-series **factor observations** that can feed alpha research, for example daily news sentiment per industry keyword.

A factor observation is keyed by:

- `feature_name`: stored factor name, e.g. `news.sentiment.industry` (kept as `feature_name` for storage compatibility)
- `entity_id`: target entity, e.g. `semiconductors`, `AAPL`, or `KRW`
- `timestamp`: ISO date/datetime

Each observation stores a numeric `value`, optional JSON `metadata`, optional `source`, and write timestamp.

Local SQLite usage:

```bash
qfa factors put \
  --name news.sentiment.industry \
  --entity semiconductors \
  --timestamp 2026-07-01 \
  --value 0.55 \
  --metadata-json '{"keyword":"chips"}' \
  --source manual

qfa factors get \
  --name news.sentiment.industry \
  --entity semiconductors \
  --timestamp 2026-07-01

qfa factors query \
  --name news.sentiment.industry \
  --entity semiconductors \
  --start 2026-07-01 \
  --end 2026-07-31
```

`qfa features ...` remains available as a compatibility alias.

Bulk import CSV:

```csv
feature_name,entity_id,timestamp,value,metadata_json,source
news.sentiment.industry,semiconductors,2026-07-01,0.55,"{""keyword"":""chips""}",daily-news-pipeline
```

```bash
qfa factors import-csv features.csv
```

AWS/DynamoDB usage:

```bash
export QFA_AWS_REGION=us-west-2

aws cloudformation deploy \
  --stack-name qfa-feature-database \
  --template-file infra/aws/qfa-feature-database.yaml \
  --parameter-overrides TableName=qfa-feature-observations \
  --region "$QFA_AWS_REGION"

export QFA_FACTOR_BACKEND=dynamodb
export QFA_FACTOR_TABLE=qfa-feature-observations

qfa factors put --backend dynamodb --name news.sentiment.industry --entity semiconductors --timestamp 2026-07-01 --value 0.55
qfa factors query --backend dynamodb --name news.sentiment.industry --start 2026-07-01 --end 2026-07-31
```

The DynamoDB table uses `feature_entity = feature_name#entity_id` as the partition key, `timestamp` as the sort key, a `FeatureTimestampIndex` GSI for cross-entity factor queries, pay-per-request billing, server-side encryption, and point-in-time recovery.

## Factor Repository MVP

A factor repository is a local directory tree containing `factor.toml` manifests and Python calculators. Configure one or more roots with `factor_repository.repository_paths` in `qfa.toml` or `QFA_FACTOR_REPOSITORY_PATHS`.

Recommended layout:

```text
factors/
  price.momentum.20d/
    factor.toml
    calculator.py
```

Minimal `factor.toml`:

```toml
schema_version = 1
name = "price.momentum.20d"
title = "20-day price momentum"
description = "Trailing close-to-close return."
version = "0.1.0"
entity_type = "symbol"
frequency = "1d"
tags = ["price", "momentum"]

[calculator]
module = "calculator.py"
function = "compute"

[outputs]
factor_name = "price.momentum.20d"
value_type = "float"
```

Calculator contract:

```python
from quant_for_agent.factors import FactorResult


def compute(context):
    # context has manifest, start, end, entities, factor_store, and metadata
    return [
        FactorResult(entity_id=symbol, timestamp=context.end, value=0.0)
        for symbol in context.entities
    ]
```

Dictionaries with `entity_id`, `timestamp`, `value`, and optional `metadata` are also accepted. qfa writes results to the existing Factor Store as `FeatureObservation` rows using `outputs.factor_name` (or the manifest `name`) and adds provenance metadata: factor name, version, calculator module/function, and computed timestamp.

Repository workflow:

```bash
qfa --config ./qfa.toml factors list
qfa --config ./qfa.toml factors describe price.momentum.20d
qfa --config ./qfa.toml factors compute price.momentum.20d \
  --symbols AAPL,MSFT \
  --start 2026-01-01 \
  --end 2026-01-31
```

`--symbols` also has a `--entities` alias for non-ticker factor entities such as countries, sectors, or industries; entity IDs are preserved exactly as provided.

This MVP intentionally does **not** auto-refresh factors from backtests, daemon runs, or alpha dependency declarations. Alpha-sidecar dependency parsing, freshness checks, dependency graph sorting, and `update-required` are future work.

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
# Optional for equity data: use IEX data for accounts without recent SIP entitlement.
export ALPACA_DATA_FEED=iex
```

Equity remains the default asset class. For Alpaca spot crypto data, pass `--asset-class crypto` and use Alpaca's slash crypto symbol format, for example `BTC/USD,ETH/USD`:

```bash
qfa backtest run models/crypto_momentum.py \
  --asset-class crypto \
  --symbols BTC/USD,ETH/USD \
  --start 2024-01-01 \
  --end 2024-06-01 \
  --fee-maker-bps 0 \
  --fee-taker-bps 25 \
  --fill-mix taker

qfa models add models/crypto_momentum.py \
  --name crypto-momentum \
  --asset-class crypto \
  --allocation 0.05 \
  --symbols BTC/USD,ETH/USD
```

Crypto backtest results include `asset_class: crypto`, `asset_bucket: crypto`, `crypto_label: true`, and a `fee_model` object with `maker_bps`, `taker_bps`, `fill_mix`, and the effective fee bps applied to turnover. Use `--fill-mix maker`, `--fill-mix taker`, or `--fill-mix mixed` to apply a per-turnover fee assumption; `unknown` records the fee inputs but applies 0 bps by default. Equity/ETF backtests keep `asset_class: equity` by default. `ALPACA_DATA_FEED` is only applied to equity `StockBarsRequest`; crypto requests use Alpaca's `CryptoHistoricalDataClient` / `CryptoBarsRequest` path.

Order placement requires passing `--submit-orders` to the daemon. With `ALPACA_PAPER=true`, orders go to the Alpaca paper account. With `ALPACA_PAPER=false`, live brokerage orders also require `--allow-live-brokerage`. Use paper trading first.

Daemon runs include the active registered asset classes in startup output without printing credentials. Crypto models use the same default simulation/no-submit behavior as equity models, request 24/7 Alpaca crypto bars through `CryptoHistoricalDataClient`, and submit paper/live crypto market orders only behind the existing order interlocks. Crypto order requests validate Alpaca's slash-delimited symbol format and use `TimeInForce.GTC`; equity orders continue to use `TimeInForce.DAY`. qfa skips a symbol if active models disagree on its asset class, preventing a crypto symbol from being silently treated as an equity order.

List registered models by asset class when separating crypto from equities/ETFs:

```bash
qfa models list --asset-class crypto
qfa models list --asset-class equity
```
