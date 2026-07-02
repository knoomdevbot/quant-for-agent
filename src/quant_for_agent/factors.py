from __future__ import annotations

import importlib.util
import tomllib
from dataclasses import asdict, dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any, Iterable, cast

from .features import FeatureObservation, FeatureStore, utc_now_iso


class FactorRepositoryError(ValueError):
    """Raised when factor repository discovery or execution fails."""


@dataclass(frozen=True)
class FactorManifest:
    schema_version: int
    name: str
    title: str
    description: str
    version: str
    entity_type: str
    frequency: str
    tags: tuple[str, ...]
    calculator_module: str
    calculator_function: str
    output_factor_name: str
    output_value_type: str
    dependencies: dict[str, Any] = field(default_factory=dict)
    freshness: dict[str, Any] = field(default_factory=dict)
    path: Path | None = None

    @classmethod
    def from_file(cls, path: str | Path) -> "FactorManifest":
        manifest_path = Path(path).expanduser()
        try:
            with manifest_path.open("rb") as handle:
                payload = tomllib.load(handle)
        except tomllib.TOMLDecodeError as exc:
            raise FactorRepositoryError(f"Malformed factor manifest {manifest_path}: {exc}") from exc
        except OSError as exc:
            raise FactorRepositoryError(f"Could not read factor manifest {manifest_path}: {exc}") from exc
        if not isinstance(payload, dict):
            raise FactorRepositoryError(f"Malformed factor manifest {manifest_path}: expected TOML object")
        return cls.from_dict(payload, path=manifest_path)

    @classmethod
    def from_dict(cls, payload: dict[str, Any], *, path: Path | None = None) -> "FactorManifest":
        location = f" {path}" if path else ""

        def require(name: str, expected_type: type | tuple[type, ...] = str) -> Any:
            value = payload.get(name)
            if value in (None, ""):
                raise FactorRepositoryError(f"Malformed factor manifest{location}: missing required field '{name}'")
            if not isinstance(value, expected_type):
                raise FactorRepositoryError(f"Malformed factor manifest{location}: field '{name}' has invalid type")
            return value

        schema_version = require("schema_version", int)
        if schema_version != 1:
            raise FactorRepositoryError(
                f"Malformed factor manifest{location}: unsupported schema_version {schema_version}; expected 1"
            )
        calculator = payload.get("calculator")
        if not isinstance(calculator, dict):
            raise FactorRepositoryError(f"Malformed factor manifest{location}: missing required table 'calculator'")
        outputs = payload.get("outputs")
        if not isinstance(outputs, dict):
            raise FactorRepositoryError(f"Malformed factor manifest{location}: missing required table 'outputs'")

        calculator_module = calculator.get("module")
        calculator_function = calculator.get("function")
        output_factor_name = outputs.get("factor_name") or payload.get("name")
        output_value_type = outputs.get("value_type") or "float"
        for field_name, value in (
            ("calculator.module", calculator_module),
            ("calculator.function", calculator_function),
            ("outputs.factor_name", output_factor_name),
            ("outputs.value_type", output_value_type),
        ):
            if not isinstance(value, str) or not value.strip():
                raise FactorRepositoryError(
                    f"Malformed factor manifest{location}: missing required field '{field_name}'"
                )

        tags = payload.get("tags", [])
        if tags is None:
            tags = []
        if not isinstance(tags, list) or any(not isinstance(item, str) for item in tags):
            raise FactorRepositoryError(f"Malformed factor manifest{location}: field 'tags' must be a list of strings")

        dependencies = payload.get("dependencies", {})
        if dependencies is None:
            dependencies = {}
        if not isinstance(dependencies, dict):
            raise FactorRepositoryError(f"Malformed factor manifest{location}: table 'dependencies' must be an object")
        freshness = payload.get("freshness", {})
        if freshness is None:
            freshness = {}
        if not isinstance(freshness, dict):
            raise FactorRepositoryError(f"Malformed factor manifest{location}: table 'freshness' must be an object")

        calculator_module_text = cast(str, calculator_module).strip()
        calculator_function_text = cast(str, calculator_function).strip()
        output_factor_name_text = cast(str, output_factor_name).strip()
        output_value_type_text = cast(str, output_value_type).strip()

        return cls(
            schema_version=schema_version,
            name=str(require("name")).strip(),
            title=str(require("title")).strip(),
            description=str(require("description")).strip(),
            version=str(require("version")).strip(),
            entity_type=str(require("entity_type")).strip(),
            frequency=str(require("frequency")).strip(),
            tags=tuple(tags),
            calculator_module=calculator_module_text,
            calculator_function=calculator_function_text,
            output_factor_name=output_factor_name_text,
            output_value_type=output_value_type_text,
            dependencies=dependencies,
            freshness=freshness,
            path=path,
        )

    @property
    def manifest_dir(self) -> Path:
        if self.path is None:
            return Path.cwd()
        return self.path.parent

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["path"] = str(self.path) if self.path else None
        payload["tags"] = list(self.tags)
        payload["calculator"] = {
            "module": payload.pop("calculator_module"),
            "function": payload.pop("calculator_function"),
        }
        payload["outputs"] = {
            "factor_name": payload.pop("output_factor_name"),
            "value_type": payload.pop("output_value_type"),
        }
        return payload


@dataclass(frozen=True)
class FactorComputeContext:
    manifest: FactorManifest
    start: str
    end: str
    entities: tuple[str, ...]
    factor_store: FeatureStore
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FactorResult:
    entity_id: str
    timestamp: str
    value: float
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_obj(cls, obj: "FactorResult | dict[str, Any]") -> "FactorResult":
        if isinstance(obj, FactorResult):
            return obj
        if not isinstance(obj, dict):
            raise FactorRepositoryError("Calculator results must be FactorResult instances or dictionaries")
        try:
            entity_id = obj["entity_id"]
            timestamp = obj["timestamp"]
            value = obj["value"]
        except KeyError as exc:
            raise FactorRepositoryError(f"Calculator result missing required field '{exc.args[0]}'") from exc
        metadata = obj.get("metadata", {})
        if metadata is None:
            metadata = {}
        if not isinstance(metadata, dict):
            raise FactorRepositoryError("Calculator result field 'metadata' must be an object")
        return cls(entity_id=str(entity_id), timestamp=str(timestamp), value=float(value), metadata=metadata)


@dataclass(frozen=True)
class ComputeSummary:
    manifest: FactorManifest
    count: int
    observations: list[FeatureObservation]


def discover_manifests(repository_paths: Iterable[str | Path]) -> list[FactorManifest]:
    manifests: list[FactorManifest] = []
    seen: dict[str, Path | None] = {}
    for repository_path in repository_paths:
        root = Path(repository_path).expanduser()
        if not root.exists():
            continue
        manifest_paths = [root] if root.is_file() and root.name == "factor.toml" else sorted(root.rglob("factor.toml"))
        for manifest_path in manifest_paths:
            manifest = FactorManifest.from_file(manifest_path)
            if manifest.name in seen:
                raise FactorRepositoryError(
                    "Duplicate factor manifest name "
                    f"'{manifest.name}' found at {manifest.path} and {seen[manifest.name]}"
                )
            seen[manifest.name] = manifest.path
            manifests.append(manifest)
    return sorted(manifests, key=lambda item: item.name)


def get_manifest(repository_paths: Iterable[str | Path], name: str) -> FactorManifest:
    manifests = discover_manifests(repository_paths)
    for manifest in manifests:
        if manifest.name == name:
            return manifest
    searched = ", ".join(str(Path(path).expanduser()) for path in repository_paths) or "<none configured>"
    raise FactorRepositoryError(f"Factor '{name}' not found in repository paths: {searched}")


def _load_calculator_module(manifest: FactorManifest) -> ModuleType:
    module_path = (manifest.manifest_dir / manifest.calculator_module).expanduser()
    if not module_path.exists():
        raise FactorRepositoryError(
            f"Calculator module for factor '{manifest.name}' not found: {module_path}"
        )
    spec = importlib.util.spec_from_file_location(
        f"qfa_factor_{manifest.name.replace('.', '_').replace('-', '_')}", module_path
    )
    if spec is None or spec.loader is None:
        raise FactorRepositoryError(f"Could not load calculator module: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def compute_factor(
    manifest: FactorManifest,
    *,
    start: str,
    end: str,
    entities: Iterable[str],
    factor_store: FeatureStore,
    metadata: dict[str, Any] | None = None,
) -> ComputeSummary:
    module = _load_calculator_module(manifest)
    function = getattr(module, manifest.calculator_function, None)
    if not callable(function):
        raise FactorRepositoryError(
            f"Calculator function '{manifest.calculator_function}' not found in {manifest.calculator_module}"
        )
    computed_at = utc_now_iso()
    provenance = {
        "factor_name": manifest.name,
        "factor_version": manifest.version,
        "calculator_module": manifest.calculator_module,
        "calculator_function": manifest.calculator_function,
        "computed_at": computed_at,
    }
    context = FactorComputeContext(
        manifest=manifest,
        start=start,
        end=end,
        entities=tuple(entities),
        factor_store=factor_store,
        metadata={**(metadata or {}), "provenance": provenance},
    )
    raw_results = function(context)
    if raw_results is None:
        raw_results = []
    if not isinstance(raw_results, list | tuple):
        raise FactorRepositoryError("Calculator must return a list of FactorResult objects or dictionaries")

    observations: list[FeatureObservation] = []
    for raw in raw_results:
        result = FactorResult.from_obj(raw)
        observation_metadata = {**result.metadata, "provenance": provenance}
        observation = FeatureObservation(
            feature_name=manifest.output_factor_name or manifest.name,
            entity_id=result.entity_id,
            timestamp=result.timestamp,
            value=result.value,
            metadata=observation_metadata,
            source=f"factor:{manifest.name}",
            created_at=computed_at,
        )
        observations.append(factor_store.put(observation))
    return ComputeSummary(manifest=manifest, count=len(observations), observations=observations)
