# Custom Feature Database Tech Spec

## Current architecture
qfa is a Python/Typer CLI. Local durable state for backtests, registered alpha models, daemon status, and trade events lives in SQLite through `quant_for_agent.storage.Store`. No AWS database code exists today.

## Proposed architecture
Add a dedicated feature-store module with a small backend interface:

- `FeatureObservation`: normalized observation object.
- `SQLiteFeatureStore`: local/dev/test backend, stored in the existing qfa SQLite DB unless `--db` overrides it.
- `DynamoDBFeatureStore`: AWS backend selected by `--backend dynamodb` or `QFA_FEATURE_BACKEND=dynamodb`.

Add a `qfa features` command group:

- `put`: upsert one observation.
- `get`: read one observation.
- `query`: date-ranged read.
- `import-csv`: upsert many observations.

## Data model
Canonical fields:

- `feature_name`: stable signal name, e.g. `news.sentiment.industry`.
- `entity_id`: target entity, e.g. `semiconductors`, `AAPL`, `KRW`.
- `timestamp`: ISO-8601 date/datetime string, normalized to UTC-compatible ISO where possible.
- `value`: numeric feature value.
- `metadata`: JSON object for provenance/dimensions.
- `source`: optional producer/source label.
- `created_at`: write time.

SQLite table:

```sql
feature_observations(
  feature_name TEXT,
  entity_id TEXT,
  timestamp TEXT,
  value REAL,
  metadata_json TEXT,
  source TEXT,
  created_at TEXT,
  PRIMARY KEY(feature_name, entity_id, timestamp)
)
```

DynamoDB table:

- Table name default: `qfa-feature-observations`.
- Partition key: `feature_entity` = `<feature_name>#<entity_id>`.
- Sort key: `timestamp`.
- GSI `FeatureTimestampIndex`: partition key `feature_name`, sort key `timestamp` for cross-entity feature queries.
- Billing: PAY_PER_REQUEST.
- PITR enabled.
- SSE enabled.

## Config
Environment variables:

- `QFA_FEATURE_BACKEND`: `sqlite` or `dynamodb`; default `sqlite`.
- `QFA_FEATURE_TABLE`: DynamoDB table name; default `qfa-feature-observations`.
- `QFA_AWS_REGION` or `AWS_REGION` / `AWS_DEFAULT_REGION`: DynamoDB region.

## Security / operations
- No secrets are committed; DynamoDB uses ambient AWS credentials.
- IAM needs only table-scoped read/write actions for normal CLI use.
- Live AWS table creation is blocked until the current `devbot` IAM identity receives DynamoDB permissions or the user creates the table from the committed CloudFormation template.

## Tests
- Unit tests for SQLite put/get/query/import behavior.
- Unit tests for DynamoDB request shape using a fake in-memory client.
- CLI tests with `CliRunner` and temp SQLite DB.
- CLI smoke command sequence after implementation.
