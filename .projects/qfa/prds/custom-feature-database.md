# Custom Feature Database PRD

## Problem
Quant agents need a durable place to store custom time-series signals that can later feed alpha research and models. Examples include daily news sentiment per industry keyword, macro surprise scores per country, or alternative-data features per ticker.

## Desired outcome
A qfa-owned AWS database stores feature observations, and qfa exposes CLI commands to write/read those observations without requiring each alpha project to invent its own storage shape.

## MVP behavior
- Store observations keyed by `feature_name`, `entity_id`, and `timestamp`.
- Each observation has a numeric `value`, optional `metadata`, optional `source`, and write timestamp.
- Commands support local SQLite for deterministic tests/dev and DynamoDB for the AWS-owned production database.
- CSV import supports bulk writes from simple research pipelines.

## Non-goals
- No trading/order placement changes.
- No feature engineering DSL yet.
- No automatic alpha-context integration in this slice; models can call qfa read commands or use the Python feature-store module in a later slice.

## Acceptance criteria
- `qfa features put` writes one observation.
- `qfa features import-csv` writes many observations.
- `qfa features get` returns one observation or exits nonzero when absent.
- `qfa features query` returns a date-ranged time series for one feature/entity, and can query all entities for a feature when the backend supports it.
- AWS DynamoDB table definition is committed with least-surprise billing and data model docs.
- Tests and CLI smoke pass locally without AWS credentials.

## Metrics / feedback
This is developer-facing infrastructure. Success is measured by CLI usage and whether alpha model workflows can persist/retrieve custom features without bespoke databases. Feedback channel is the user's direct QFA iteration thread and repo issues under `.projects/qfa/issues/`.
