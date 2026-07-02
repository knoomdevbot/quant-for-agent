# QFA-002 — Factor Store config file and factor repository

## Original request

User accepted “factor” as the qfa term for custom quant research data streams and asked to add config-file support because env vars are becoming too many. User also asked how agents should populate and manage the factor database, including whether qfa should support a factor repository with definitions and modules to calculate factor values, and how alphas should update required factors before running.

## Product direction

qfa should evolve from a passive factor observation store into a small **factor management workflow**:

1. A config file defines default qfa paths, factor backend/table/region, Alpaca defaults, notification settings, and factor repository location.
2. A factor repository stores versioned factor definitions and calculation modules.
3. qfa can discover factor definitions, run factor calculators for a period/entity universe, write factor observations to the Factor Store, and ensure required factors are fresh before running dependent alpha models.

## Scope for first implementation slice

- Add config-file loading with clear precedence: CLI option > env var > config file > built-in default.
- Add `qfa config show` to print the resolved config with secrets redacted.
- Add `qfa factors` as the preferred alias for current `qfa features` commands.
- Keep `qfa features` as a compatibility alias.
- Define factor repository architecture in docs/specs.

## Scope for next implementation slice

- Add factor repository commands and manifests:
  - `qfa factors list`
  - `qfa factors describe NAME`
  - `qfa factors compute NAME --start ... --end ... --entities ...`
  - `qfa factors update-required MODEL --start ... --end ...`
- Add alpha dependency metadata, likely as sidecar `alpha.yaml` or module-level `REQUIRED_FACTORS`.

## Acceptance criteria

- Config defaults can be read from `~/.qfa/config.toml` or an explicit `--config`/`QFA_CONFIG` path.
- Existing env vars continue to work and override config file values.
- CLI flags remain highest precedence.
- `qfa config show` returns JSON with no secrets in plaintext.
- `qfa factors ...` works as the canonical command group for factor observations.
- Durable PRD/spec/milestone docs define factor repository concepts, manifest schema, compute contract, freshness checks, and alpha dependency flow.

## Evidence required

- Unit tests for config precedence and secret redaction.
- CLI tests for `qfa config show` and `qfa factors` alias commands.
- `pytest` passes.
- `ruff check .` passes.
- README and project docs updated.
