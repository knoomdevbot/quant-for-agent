# QFA-003 — Factor Repository MVP

## Status

Done

## Original request

User said: “Go ahead” after the proposed next slice for a qfa Factor Repository:

1. Add `factor.toml` manifest support.
2. Add configured `factor_repository.repository_paths`.
3. Add `qfa factors list`, `qfa factors describe NAME`, `qfa factors compute NAME --start --end --symbols ...`.
4. Define a calculator contract.
5. Add freshness checks.
6. Defer alpha dependency integration unless the MVP remains small.

## Scope

Implement the smallest useful Factor Repository MVP that lets agents discover factor manifests, describe them, run local Python calculators, and persist computed factor observations into the existing Factor Store.

## Acceptance criteria

- `qfa factors list` discovers `factor.toml` manifests from configured repository paths.
- `qfa factors describe FACTOR_NAME` prints manifest metadata as JSON.
- Duplicate factor names fail clearly during discovery/lookup.
- Malformed or incomplete manifests fail with actionable messages.
- `qfa factors compute FACTOR_NAME --symbols AAPL,MSFT --start YYYY-MM-DD --end YYYY-MM-DD` loads the factor calculator, executes it, and writes returned observations to the configured Factor Store.
- Calculator context includes manifest, start, end, entities, factor store, and metadata.
- Calculator result contract supports entity ID, timestamp, numeric value, and metadata.
- Written observations include provenance metadata such as factor name, version, calculator module/function, and computed timestamp.
- Tests cover list/describe, malformed manifests, duplicate factors, calculator execution, and writes to the SQLite Factor Store.
- README and project docs explain the MVP workflow and explicitly note that alpha dependency auto-refresh is future work.

## Out of scope for this MVP

- Automatic factor refresh inside backtests/daemon.
- Alpha sidecar dependency files and `update-required`.
- Dependency graph sorting/cycle detection beyond manifest field parsing.
- Remote factor repositories.
- DynamoDB integration beyond using the existing Factor Store abstraction.

## Evidence required

- Changed files and commit hash.
- Targeted and full test output.
- PR URL if pushed to GitHub.
