import pytest
from typer.testing import CliRunner

from quant_for_agent import cli
from quant_for_agent.storage import Store


class CapturingDaemon:
    configs = []

    def __init__(self, store, alpaca, config):
        self.store = store
        self.alpaca = alpaca
        self.config = config
        self.__class__.configs.append(config)

    def run(self):
        return None


class FakeAlpacaGateway:
    def __init__(self):
        return None


@pytest.fixture(autouse=True)
def isolate_daemon_cli(monkeypatch, tmp_path):
    CapturingDaemon.configs = []
    monkeypatch.setattr(cli, "TradingDaemon", CapturingDaemon)
    monkeypatch.setattr(cli, "AlpacaGateway", FakeAlpacaGateway)
    monkeypatch.setenv("ALPACA_API_KEY", "paper-key")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "paper-secret")
    yield


def test_daemon_run_defaults_to_explicit_no_submit_simulation(tmp_path):
    result = CliRunner().invoke(cli.app, ["daemon", "run", "--once", "--db", str(tmp_path / "qfa.sqlite3")])

    assert result.exit_code == 0
    assert CapturingDaemon.configs[-1].dry_run is True
    assert "SIMULATION ONLY: no Alpaca orders will be submitted" in result.output


def test_daemon_submit_orders_uses_alpaca_paper_without_live_flag(monkeypatch, tmp_path):
    monkeypatch.setenv("ALPACA_PAPER", "true")

    result = CliRunner().invoke(
        cli.app,
        ["daemon", "run", "--submit-orders", "--once", "--db", str(tmp_path / "qfa.sqlite3")],
    )

    assert result.exit_code == 0
    assert CapturingDaemon.configs[-1].dry_run is False
    assert "Submitting orders to Alpaca paper account" in result.output


def test_daemon_deprecated_flags_cannot_submit_orders_without_submit_orders(monkeypatch, tmp_path):
    monkeypatch.setenv("ALPACA_PAPER", "true")

    result = CliRunner().invoke(
        cli.app,
        [
            "daemon",
            "run",
            "--no-dry-run",
            "--live",
            "--once",
            "--db",
            str(tmp_path / "qfa.sqlite3"),
        ],
    )

    assert result.exit_code == 0
    assert CapturingDaemon.configs[-1].dry_run is True
    assert "SIMULATION ONLY: no Alpaca orders will be submitted" in result.output


def test_daemon_submit_orders_blocks_live_brokerage_without_explicit_interlock(monkeypatch, tmp_path):
    monkeypatch.setenv("ALPACA_PAPER", "false")

    result = CliRunner().invoke(
        cli.app,
        ["daemon", "run", "--submit-orders", "--once", "--db", str(tmp_path / "qfa.sqlite3")],
    )

    assert result.exit_code != 0
    assert CapturingDaemon.configs == []
    assert "Refusing to submit live brokerage orders" in result.output


def test_daemon_submit_orders_does_not_allow_deprecated_live_flag_as_live_interlock(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("ALPACA_PAPER", "false")

    result = CliRunner().invoke(
        cli.app,
        [
            "daemon",
            "run",
            "--submit-orders",
            "--live",
            "--once",
            "--db",
            str(tmp_path / "qfa.sqlite3"),
        ],
    )

    assert result.exit_code != 0
    assert CapturingDaemon.configs == []
    assert "Refusing to submit live brokerage orders" in result.output


def test_daemon_submit_orders_allows_live_brokerage_with_explicit_interlock(monkeypatch, tmp_path):
    monkeypatch.setenv("ALPACA_PAPER", "false")

    result = CliRunner().invoke(
        cli.app,
        [
            "daemon",
            "run",
            "--submit-orders",
            "--allow-live-brokerage",
            "--once",
            "--db",
            str(tmp_path / "qfa.sqlite3"),
        ],
    )

    assert result.exit_code == 0
    assert CapturingDaemon.configs[-1].dry_run is False
    assert "Submitting orders to Alpaca live brokerage account" in result.output


def test_daemon_run_logs_active_crypto_asset_class_without_submitting(tmp_path):
    db_path = tmp_path / "qfa.sqlite3"
    model_path = tmp_path / "crypto_model.py"
    model_path.write_text("def generate_signals(context):\n    return {'BTC/USD': 1.0}\n")
    Store(db_path).upsert_model("crypto", str(model_path), 0.05, ["BTC/USD"], asset_class="crypto")

    result = CliRunner().invoke(cli.app, ["daemon", "run", "--once", "--db", str(db_path)])

    assert result.exit_code == 0
    assert CapturingDaemon.configs[-1].dry_run is True
    assert "active_asset_classes=crypto" in result.output


def test_daemon_submit_orders_logs_paper_and_active_crypto_asset_class(monkeypatch, tmp_path):
    monkeypatch.setenv("ALPACA_PAPER", "true")
    db_path = tmp_path / "qfa.sqlite3"
    model_path = tmp_path / "crypto_model.py"
    model_path.write_text("def generate_signals(context):\n    return {'BTC/USD': 1.0}\n")
    Store(db_path).upsert_model("crypto", str(model_path), 0.05, ["BTC/USD"], asset_class="crypto")

    result = CliRunner().invoke(
        cli.app,
        ["daemon", "run", "--submit-orders", "--once", "--db", str(db_path)],
    )

    assert result.exit_code == 0
    assert CapturingDaemon.configs[-1].dry_run is False
    assert "Submitting orders to Alpaca paper account" in result.output
    assert "active_asset_classes=crypto" in result.output
