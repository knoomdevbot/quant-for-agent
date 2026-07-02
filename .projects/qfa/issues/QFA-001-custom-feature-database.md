# QFA-001 — Custom feature database

## Original request
User needs qfa to support using a custom feature database. A feature is a time-series style signal used to build alpha models, e.g. daily news sentiment for each industry keyword. The user wants:

1. A qfa-owned database running on AWS.
2. qfa commands to read/write to the database.

## Scope
- Add a durable feature data model for time-series feature observations.
- Add qfa CLI commands for writing and reading feature observations.
- Add AWS infrastructure definition for a qfa-owned feature database.
- Keep local/test usage deterministic without requiring AWS credentials.

## Acceptance criteria
- `qfa features put` can write one observation.
- `qfa features import-csv` can write multiple observations from CSV.
- `qfa features query` can read observations by feature name, entity id, and date range.
- `qfa features get` can read one observation.
- CLI supports local SQLite for tests/dev and DynamoDB for AWS by configuration.
- AWS infra artifact defines the owned database with safe defaults.
- Tests cover local read/write/query behavior and DynamoDB request shape with a fake client.
- README documents setup and command usage.

## Access / blockers
- GitHub CLI access is verified.
- AWS identity is verified as `arn:aws:iam::061039762362:user/devbot`.
- Current AWS identity lacks DynamoDB permissions in `us-west-2`: `dynamodb:ListTables` was denied. Infrastructure can be implemented and documented, but live AWS table creation requires owner action or additional IAM permissions.

## Evidence required
- `pytest` — passed, 78 tests.
- `ruff check .` — passed.
- `git diff --check` — passed.
- CLI smoke with local SQLite feature store — passed.
- CloudFormation template validation — passed.
- AWS deploy/check evidence, or explicit owner-action blocker checklist if permissions remain missing — deploy attempted and blocked by missing DynamoDB IAM permissions; rollback stack was deleted.

## Owner action needed for live AWS database
Grant `arn:aws:iam::061039762362:user/devbot` permissions to deploy/use the table, or deploy `infra/aws/qfa-feature-database.yaml` yourself. Minimum normal runtime actions are documented in `.projects/qfa/runbooks/feature-database-aws.md`; CloudFormation deployment additionally needs stack create/update and DynamoDB table create/describe/update/delete permissions.
