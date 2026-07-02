import json

from typer.testing import CliRunner

from quant_for_agent import cli
from quant_for_agent.config import load_qfa_config, redact_config


def test_config_file_loads_and_env_overrides(tmp_path, monkeypatch):
    config_path = tmp_path / "qfa.toml"
    config_path.write_text(
        """
[core]
home = "./qfa-home"
db = "./from-config.sqlite3"

[factor_store]
backend = "dynamodb"
table = "from-config-table"
region = "us-west-2"

[alpaca]
api_key = "config-key"
secret_key = "config-secret"
paper = false

[notifications.email]
to = ["ops@example.com"]
smtp_url = "smtp://user:pass@smtp.example.com:587?from=sender@example.com"

[factor_repository]
repository_paths = ["./factors"]
max_staleness_seconds = 86400
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.setenv("QFA_FACTOR_TABLE", "from-env-table")
    monkeypatch.setenv("ALPACA_PAPER", "true")

    config = load_qfa_config(config_path=config_path)

    assert config.core.db == tmp_path / "from-config.sqlite3"
    assert config.factor_store.backend == "dynamodb"
    assert config.factor_store.table == "from-env-table"
    assert config.alpaca.api_key == "config-key"
    assert config.alpaca.paper is True
    assert config.email.to == ("ops@example.com",)
    assert config.factor_repository.repository_paths == (tmp_path / "factors",)
    assert config.factor_repository.max_staleness_seconds == 86400


def test_cli_overrides_env_and_config(tmp_path, monkeypatch):
    config_path = tmp_path / "qfa.toml"
    config_path.write_text(
        """
[core]
db = "./from-config.sqlite3"

[factor_store]
backend = "dynamodb"
table = "from-config-table"
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.setenv("QFA_DB", str(tmp_path / "from-env.sqlite3"))

    config = load_qfa_config(
        config_path=config_path,
        cli_overrides={"core.db": tmp_path / "from-cli.sqlite3", "factor_store.backend": "sqlite"},
    )

    assert config.core.db == tmp_path / "from-cli.sqlite3"
    assert config.factor_store.backend == "sqlite"
    assert config.factor_store.table == "from-config-table"


def test_redact_config_hides_secrets(tmp_path):
    config_path = tmp_path / "qfa.toml"
    config_path.write_text(
        """
[alpaca]
api_key = "abc12345"
secret_key = "super-secret"

[notifications.email]
smtp_url = "smtp://user:pass@smtp.example.com:587"
smtp_password = "mail-secret"
""".strip(),
        encoding="utf-8",
    )

    redacted = redact_config(load_qfa_config(config_path=config_path))

    assert redacted["alpaca"]["api_key"] == "********2345"
    assert redacted["alpaca"]["secret_key"] == "********cret"
    assert redacted["email"]["smtp_password"] == "********cret"
    assert redacted["email"]["smtp_url"] == "smtp://********@smtp.example.com:587"


def test_qfa_config_show_uses_config_file_and_redacts(tmp_path):
    config_path = tmp_path / "qfa.toml"
    config_path.write_text(
        """
[core]
db = "./configured.sqlite3"

[alpaca]
api_key = "abc12345"
secret_key = "super-secret"

[factor_store]
backend = "sqlite"
table = "configured-table"
""".strip(),
        encoding="utf-8",
    )

    result = CliRunner().invoke(cli.app, ["--config", str(config_path), "config", "show"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["core"]["db"] == str(tmp_path / "configured.sqlite3")
    assert payload["alpaca"]["api_key"] == "********2345"
    assert payload["factor_store"]["table"] == "configured-table"


def test_explicit_missing_config_fails(tmp_path):
    result = CliRunner().invoke(cli.app, ["--config", str(tmp_path / "missing.toml"), "config", "show"])

    assert result.exit_code == 2
    assert "qfa config file not found" in result.output
