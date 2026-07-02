import json

import pytest
from typer.testing import CliRunner

from quant_for_agent import cli
from quant_for_agent.factors import FactorRepositoryError, discover_manifests
from quant_for_agent.features import SQLiteFeatureStore


MANIFEST_TEMPLATE = """
schema_version = 1
name = "{name}"
title = "Test Factor"
description = "A test factor."
version = "0.1.0"
entity_type = "symbol"
frequency = "1d"
tags = ["test"]

[calculator]
module = "calculator.py"
function = "compute"

[outputs]
factor_name = "{output_name}"
value_type = "float"

[dependencies]
factors = []
data = []

[freshness]
max_age_seconds = 86400
""".lstrip()


def write_factor(repo_path, name="test.factor", output_name=None, calculator_source=None, dir_name=None):
    factor_dir = repo_path / (dir_name or name)
    factor_dir.mkdir(parents=True)
    output_name = output_name or name
    (factor_dir / "factor.toml").write_text(
        MANIFEST_TEMPLATE.format(name=name, output_name=output_name),
        encoding="utf-8",
    )
    (factor_dir / "calculator.py").write_text(
        calculator_source
        or """
def compute(context):
    return [
        {
            "entity_id": entity,
            "timestamp": context.end,
            "value": float(index + 1),
            "metadata": {"rank": index, "start": context.start},
        }
        for index, entity in enumerate(context.entities)
    ]
""".lstrip(),
        encoding="utf-8",
    )
    return factor_dir


def write_config(tmp_path, repo_path, db_path=None):
    db_path = db_path or (tmp_path / "qfa.sqlite3")
    config_path = tmp_path / "qfa.toml"
    config_path.write_text(
        f"""
[core]
db = "{db_path}"

[factor_repository]
repository_paths = ["{repo_path}"]

[factor_store]
backend = "sqlite"
""".lstrip(),
        encoding="utf-8",
    )
    return config_path


def test_cli_factors_list_and_describe_from_config_repository_paths(tmp_path):
    repo_path = tmp_path / "factors"
    write_factor(repo_path, name="test.factor")
    config_path = write_config(tmp_path, repo_path)
    runner = CliRunner()

    list_result = runner.invoke(cli.app, ["--config", str(config_path), "factors", "list"])
    assert list_result.exit_code == 0
    listed = json.loads(list_result.output)
    assert [item["name"] for item in listed] == ["test.factor"]
    assert listed[0]["calculator"] == {"module": "calculator.py", "function": "compute"}

    describe_result = runner.invoke(
        cli.app, ["--config", str(config_path), "factors", "describe", "test.factor"]
    )
    assert describe_result.exit_code == 0
    described = json.loads(describe_result.output)
    assert described["name"] == "test.factor"
    assert described["outputs"]["factor_name"] == "test.factor"


def test_duplicate_factor_manifests_fail(tmp_path):
    repo_path = tmp_path / "factors"
    write_factor(repo_path, name="dupe.factor", dir_name="one")
    write_factor(repo_path, name="dupe.factor", output_name="dupe.factor.v2", dir_name="two")

    with pytest.raises(FactorRepositoryError, match="Duplicate factor manifest name 'dupe.factor'"):
        discover_manifests([repo_path])


def test_malformed_manifest_missing_required_fields_fails(tmp_path):
    repo_path = tmp_path / "factors"
    bad_dir = repo_path / "bad.factor"
    bad_dir.mkdir(parents=True)
    (bad_dir / "factor.toml").write_text(
        """
schema_version = 1
name = "bad.factor"

[calculator]
module = "calculator.py"
function = "compute"

[outputs]
factor_name = "bad.factor"
value_type = "float"
""".lstrip(),
        encoding="utf-8",
    )

    with pytest.raises(FactorRepositoryError, match="missing required field 'title'"):
        discover_manifests([repo_path])


def test_cli_factors_compute_writes_observations_to_sqlite(tmp_path):
    repo_path = tmp_path / "factors"
    db_path = tmp_path / "qfa.sqlite3"
    write_factor(repo_path, name="test.factor", output_name="stored.factor")
    config_path = write_config(tmp_path, repo_path, db_path)
    runner = CliRunner()

    compute_result = runner.invoke(
        cli.app,
        [
            "--config",
            str(config_path),
            "factors",
            "compute",
            "test.factor",
            "--symbols",
            "semiconductors,AAPL",
            "--start",
            "2026-01-01",
            "--end",
            "2026-01-31",
        ],
    )

    assert compute_result.exit_code == 0, compute_result.output
    payload = json.loads(compute_result.output)
    assert payload["count"] == 2
    assert payload["output_factor_name"] == "stored.factor"

    store = SQLiteFeatureStore(db_path)
    observations = store.query("stored.factor", start="2026-01-01", end="2026-01-31")
    assert [(item.entity_id, item.timestamp, item.value) for item in observations] == [
        ("AAPL", "2026-01-31", 2.0),
        ("semiconductors", "2026-01-31", 1.0),
    ]
    provenance = observations[0].metadata["provenance"]
    assert provenance["factor_name"] == "test.factor"
    assert provenance["factor_version"] == "0.1.0"
    assert provenance["calculator_module"] == "calculator.py"
    assert provenance["calculator_function"] == "compute"
    assert "computed_at" in provenance


def test_calculator_can_return_factor_result_instances(tmp_path):
    repo_path = tmp_path / "factors"
    write_factor(
        repo_path,
        name="result.factor",
        calculator_source="""
from quant_for_agent.factors import FactorResult


def compute(context):
    return [FactorResult(entity_id="AAPL", timestamp=context.end, value=3.14, metadata={"kind": "dataclass"})]
""".lstrip(),
    )
    manifest = discover_manifests([repo_path])[0]
    store = SQLiteFeatureStore(tmp_path / "qfa.sqlite3")

    from quant_for_agent.factors import compute_factor

    summary = compute_factor(
        manifest,
        start="2026-01-01",
        end="2026-01-31",
        entities=["AAPL"],
        factor_store=store,
    )

    assert summary.count == 1
    saved = store.get("result.factor", "AAPL", "2026-01-31")
    assert saved is not None
    assert saved.value == 3.14
    assert saved.metadata["kind"] == "dataclass"
