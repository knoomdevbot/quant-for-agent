# Factor config and repository tech spec

## Status

Draft for QFA-002. The first implementation slice covers config-file support and canonical `qfa factors` command naming. The factor repository/compute workflow is specified for the next slice.

## Current architecture

qfa is a Python/Typer CLI. Before this slice, most configuration came from env vars or per-command options:

- Core paths: `QFA_HOME`, `QFA_DB`, `QFA_HEALTH_LOG`
- Alpaca: `ALPACA_API_KEY`, `ALPACA_SECRET_KEY`, `ALPACA_PAPER`, `ALPACA_DATA_FEED`
- Factor Store, previously named feature store: `QFA_FEATURE_BACKEND`, `QFA_FEATURE_TABLE`, `QFA_AWS_REGION`
- Email notifications: `QFA_NOTIFY_EMAIL_TO`, `QFA_NOTIFY_EMAIL_SMTP_URL`, split SMTP vars

The factor observation store is implemented in `src/quant_for_agent/features.py` and exposed through `qfa features`.

## Config-file architecture

### Format and path

Use TOML because qfa requires Python 3.11 and can read TOML with stdlib `tomllib`.

Default config path:

```text
~/.qfa/config.toml
```

Overrides:

```bash
qfa --config ./qfa.toml config show
QFA_CONFIG=./qfa.toml qfa config show
```

### Precedence

For each config value:

```text
CLI option > environment variable > config file > built-in default
```

### Initial schema

```toml
[core]
home = "~/.qfa"
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
api_key = ""
secret_key = ""
paper = true
data_feed = "iex"

[notifications.email]
to = ["ops@example.com"]
smtp_url = "smtps://user:APP_PASSWORD@smtp.example.com?from=qfa@example.com"
```

Secrets may be present in the config file, but env vars remain safer for credentials in shared environments.

### Config command

```bash
qfa config show
qfa --config ./qfa.toml config show
qfa config show --no-redact
```

Default output redacts secrets such as API keys, secret keys, tokens, SMTP passwords, and SMTP URLs with embedded credentials.

## Factor naming and compatibility

Canonical command group:

```bash
qfa factors put|get|query|import-csv
```

Compatibility alias:

```bash
qfa features put|get|query|import-csv
```

Canonical env vars:

```bash
QFA_FACTOR_BACKEND
QFA_FACTOR_TABLE
QFA_FACTOR_REPOSITORY_PATHS
```

Compatibility fallbacks:

```bash
QFA_FEATURE_BACKEND
QFA_FEATURE_TABLE
```

## Factor repository architecture

### Purpose

The Factor Store persists observations. A Factor Repository should manage how observations are produced:

- factor definition metadata
- Python calculator modules
- input/data requirements
- dependency graph between factors
- freshness policy
- provenance

This gives agents a stable workflow: research a factor, add its manifest/calculator/tests, compute it for a date/entity universe, and store the results.

### Recommended repository layout

```text
factors/
  price.momentum.20d/
    factor.toml
    calculator.py
    README.md
    tests/
      test_calculator.py
  news.sentiment.industry/
    factor.toml
    calculator.py
    README.md
```

Use `factor.toml` first to avoid a YAML dependency. Add YAML later only if needed.

### Manifest schema

```toml
schema_version = 1
name = "price.momentum.20d"
title = "20-day price momentum"
description = "Trailing 20 trading day close-to-close return."
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

[dependencies]
factors = []
data = ["prices"]

[freshness]
max_age_seconds = 86400
lookback_days = 30
requires_trading_day = true
```

### Calculator contract

```python
def compute(context: FactorComputeContext) -> list[FactorResult]:
    ...
```

Where `FactorComputeContext` should include:

- factor manifest
- start/end/as-of
- entities/symbols
- optional price DataFrame
- factor store accessor for dependency reads
- metadata/provenance

`FactorResult` should contain:

- `entity_id`
- `timestamp`
- `value`
- optional `metadata`

qfa converts each result into a factor observation in the existing store, adding provenance metadata such as factor name/version and computed time.

### Proposed future commands

```bash
qfa factors list
qfa factors describe price.momentum.20d
qfa factors compute price.momentum.20d --symbols AAPL,MSFT --start 2026-01-01 --end 2026-07-01
qfa factors validate
qfa factors update-required ./alphas/sector_rotation.yaml --start 2026-01-01 --end 2026-07-01
```

## Alpha dependency workflow

Alphas should declare required factors without changing the existing `generate_signals(context)` contract.

Recommended MVP: sidecar metadata file.

```toml
name = "sector_rotation_v1"
model = "sector_rotation.py"

[[required_factors]]
name = "news.sentiment.industry"
entities_from = "universe.industry"
freshness = "1d"

[[required_factors]]
name = "macro.surprise.country"
entities = ["US"]
freshness = "7d"
```

Future explicit update flow:

```bash
qfa factors update-required ./alphas/sector_rotation.toml --start 2026-01-01 --end 2026-07-01
qfa backtest run ./alphas/sector_rotation.py --require-fresh-factors ...
```

Default should be explicit and safe: do not silently run external research/calculator code inside a backtest unless the user passes a clear opt-in such as `--compute-missing-factors`.

## Tests

Implemented/current slice:

- Config file load and path expansion.
- Precedence: CLI > env > config > defaults.
- Secret redaction.
- `qfa config show` with explicit config file.
- Explicit missing config file failure.
- `qfa factors` alias for current factor observation commands.

Future repository slice:

- Manifest discovery/list/describe.
- Malformed manifest errors.
- Duplicate factor rejection.
- Dependency graph sorting and cycle detection.
- Calculator module loading.
- Compute writes observations with provenance.
- Freshness check returns missing/stale/fresh reasons.
- Alpha-required factors are detected and update-required computes or fails clearly.
