# Decision — use “factor” for custom quant research data streams

Date: 2026-07-02

## Context imported from NED-built slice

A recent implementation added qfa support for a custom time-series database under the working name “custom feature database.” The implemented slice includes:

- CLI group: `qfa features`
- Python module: `quant_for_agent.features`
- Observation model: `FeatureObservation`
- Local backend: SQLite, defaulting to the qfa SQLite database unless `--db` overrides it
- AWS backend: DynamoDB via `QFA_FEATURE_BACKEND=dynamodb`
- Default DynamoDB table: `qfa-feature-observations`
- DynamoDB key shape: `feature_entity = <feature_name>#<entity_id>` plus `timestamp` sort key
- GSI: `FeatureTimestampIndex` for cross-entity queries by feature name and timestamp
- Commands: `put`, `get`, `query`, `import-csv`
- AWS infra template: `infra/aws/qfa-feature-database.yaml`
- Current blocker: IAM user `arn:aws:iam::061039762362:user/devbot` lacks DynamoDB permissions for live deployment in `us-west-2`; local SQLite and fake-DynamoDB tests pass.

Source artifacts currently exist under `.projects/qfa/`:

- `.projects/qfa/prds/custom-feature-database.md`
- `.projects/qfa/tech-specs/custom-feature-database.md`
- `.projects/qfa/issues/QFA-001-custom-feature-database.md`
- `.projects/qfa/runbooks/feature-database-aws.md`

## Decision

Use **factor** as the product/domain term for these custom quant research data series.

Preferred names:

- Product capability: **Factor Store**
- Individual stored value: **factor observation**
- Logical time series: **factor series**
- CSV/import data: **factor observations CSV**
- Database/table docs: **factor observation store** or **factor store**

## Rationale

“Feature” is common in machine learning, but in this qfa product it is overloaded and can be confused with software product features. “Signal” is also common in quant, but qfa already uses `generate_signals(context)` for alpha model output/target weights, so using “signal” for input data would create ambiguity.

“Factor” is widely understood in quant as a measurable variable/exposure used to explain or predict returns, and it maps well to examples like sentiment, macro surprise, momentum, valuation, quality, or alternative-data scores.

## Compatibility guidance

Do not immediately break the implemented `qfa features` CLI unless a migration is planned. Recommended migration path:

1. Introduce `qfa factors` as the preferred CLI group.
2. Keep `qfa features` as a deprecated alias for at least one release.
3. Add Python aliases such as `FactorObservation` / `FactorStore` while retaining `FeatureObservation` / `FeatureStore` compatibility.
4. Prefer new environment variables for new usage, e.g. `QFA_FACTOR_BACKEND` and `QFA_FACTOR_TABLE`, while accepting old `QFA_FEATURE_*` names. Keep the existing default table `qfa-feature-observations` until a deliberate storage migration is planned.
5. Update docs/examples from “feature” to “factor,” with a short compatibility note.

## Non-decision

This decision does not rename code by itself. It records the domain language and migration direction for the next implementation slice.
