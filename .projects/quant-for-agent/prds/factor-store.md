# Factor Store PRD (renamed from Custom Feature Database)

## User problem

Quant agents need a durable, qfa-owned place to store custom numeric time-series data that can later feed alpha research and models. Examples include daily news sentiment per industry, macro surprise scores per country, valuation scores per ticker, or alternative-data scores per asset.

The previous working name, “custom feature database,” is confusing because “feature” can mean a software feature. The quant-domain term should be **factor**.

## Desired outcome

qfa exposes a **Factor Store**: a CLI- and Python-accessible store for factor observations, backed by local SQLite for deterministic development/tests and DynamoDB for an AWS-owned production database.

## Core terms

- **Factor**: a named quant variable or predictor series, e.g. `news.sentiment.industry`.
- **Factor observation**: one numeric value for a factor, entity, and timestamp.
- **Entity**: what the factor is measured against, e.g. `AAPL`, `semiconductors`, `US`, `KRW`.
- **Factor series**: observations for one factor/entity over time.
- **Factor Store**: storage/API surface for factor observations.

## MVP behavior already implemented under feature-compatible names

Current implementation uses “feature” names but the product concept maps directly to factors:

- `qfa features put` writes one factor observation.
- `qfa features import-csv` writes many observations from CSV.
- `qfa features get` reads one observation or exits nonzero when absent.
- `qfa features query` reads a date-ranged factor series and can query all entities for a factor when the backend supports it.
- SQLite backend works locally without AWS credentials.
- DynamoDB backend is implemented and selected with `--backend dynamodb` or `QFA_FEATURE_BACKEND=dynamodb`.
- AWS CloudFormation template is committed at `infra/aws/qfa-feature-database.yaml`.

## Recommended next slice

Rename product-facing language to factors without breaking existing users:

1. Add `qfa factors` as the preferred command group.
2. Keep `qfa features` as a deprecated compatibility alias.
3. Add `FactorObservation`, `FactorStore`, `SQLiteFactorStore`, and `DynamoDBFactorStore` aliases/wrappers while keeping existing feature classes importable.
4. Add `QFA_FACTOR_BACKEND` and `QFA_FACTOR_TABLE`; keep `QFA_FEATURE_BACKEND` and `QFA_FEATURE_TABLE` as fallbacks. Keep the existing default DynamoDB table name `qfa-feature-observations` until a deliberate storage migration is planned.
5. Update README, project docs, AWS runbook, and examples to say Factor Store.
6. Optional later migration: rename DynamoDB table default from `qfa-feature-observations` to `qfa-factor-observations`; avoid forcing this for existing deployments.

## Acceptance criteria for rename slice

- `qfa factors put/get/query/import-csv` works the same as current `qfa features ...` commands.
- Existing `qfa features ...` commands still pass tests and include a deprecation/help note.
- New factor-named env vars work; old feature-named env vars remain compatible.
- README describes Factor Store as the canonical term and “features” only as a compatibility alias.
- Tests cover both new factor commands and old feature aliases.

## Metrics / feedback

This is developer-facing infrastructure. Success is whether alpha research workflows can persist/retrieve factor observations without bespoke databases and without term confusion. Feedback remains the direct qfa iteration thread plus repo/project issues.

## Source context

Imported from NED-built custom feature database artifacts in `.projects/qfa/` and commit `eaf8054` (`feat: add custom feature database`).
