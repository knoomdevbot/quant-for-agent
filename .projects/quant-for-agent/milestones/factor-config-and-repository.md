# Milestone — Factor config and repository

## Goal

Make Factor Store configuration manageable for agents and define the workflow for agents to create, compute, and refresh factors used by alphas.

## Milestone 1 — Config file + factor naming

Objective: qfa can read defaults from a TOML config file while preserving existing env/CLI workflows, and users can use canonical `qfa factors` commands.

Tasks:

1. Config loader
   - Add `~/.qfa/config.toml`, `QFA_CONFIG`, and `qfa --config` support.
   - Precedence: CLI > env > config > default.
   - Acceptance: unit tests prove precedence.

2. Config inspection
   - Add `qfa config show`.
   - Redact secrets by default.
   - Acceptance: CLI test parses JSON and verifies redaction.

3. Factor command alias
   - Add `qfa factors put/get/query/import-csv` as canonical command group.
   - Keep `qfa features ...` compatibility.
   - Acceptance: CLI tests cover both groups.

4. Factor env vars
   - Prefer `QFA_FACTOR_BACKEND` and `QFA_FACTOR_TABLE`.
   - Keep `QFA_FEATURE_BACKEND` and `QFA_FEATURE_TABLE` fallbacks.
   - Acceptance: config tests cover factor env precedence.

5. Docs
   - Update README and project docs for config and factor naming.
   - Acceptance: examples show TOML config and Factor Store usage.

## Milestone 2 — Factor repository discovery

Objective: qfa can discover factor definitions before computing anything.

Tasks:

1. Manifest schema
   - Add `factor.toml` schema.
   - Acceptance: malformed manifests fail clearly.

2. Repository loader
   - Load manifests from configured `factor_repository.repository_paths`.
   - Acceptance: `qfa factors list` and `qfa factors describe NAME` work.

3. Dependency graph
   - Resolve factor dependencies topologically.
   - Acceptance: duplicate/cyclic/missing dependencies fail clearly.

## Milestone 3 — Factor compute and freshness

Objective: qfa can run factor calculators and write observations to the Factor Store.

Tasks:

1. Calculator contract
   - Define `FactorComputeContext` and `FactorResult`.
   - Acceptance: sample calculator returns observations.

2. Compute command
   - Add `qfa factors compute NAME --start --end --symbols/--entities`.
   - Acceptance: computed observations are queryable immediately.

3. Freshness check
   - Check missing/stale/fresh observations by coverage and created_at.
   - Acceptance: JSON result names reason for each update decision.

## Milestone 4 — Alpha dependency flow

Objective: alphas can declare required factors and qfa can update/check them before model runs.

Tasks:

1. Alpha sidecar metadata
   - Define `alpha.toml` with `required_factors`.
   - Acceptance: qfa can parse required factors for a model.

2. Required update command
   - Add `qfa factors update-required MODEL_OR_ALPHA_TOML --start --end`.
   - Acceptance: missing/stale factors are computed or reported with actionable errors.

3. Backtest integration
   - Add explicit `--require-fresh-factors` and optional `--compute-missing-factors`.
   - Acceptance: no existing alpha breaks; factor-aware alpha can read required factor values.
