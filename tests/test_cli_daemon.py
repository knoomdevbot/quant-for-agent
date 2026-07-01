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


def test_daemon_run_accepts_health_log_path(tmp_path):
    health_log = tmp_path / "health.jsonl"
    result = CliRunner().invoke(
        cli.app,
        [
            "daemon",
            "run",
            "--once",
            "--health-log",
            str(health_log),
            "--db",
            str(tmp_path / "qfa.sqlite3"),
        ],
    )

    assert result.exit_code == 0
    assert CapturingDaemon.configs[-1].health_log_path == str(health_log)


def test_daemon_run_accepts_email_notification_configuration(monkeypatch, tmp_path):
    monkeypatch.setenv("QFA_SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("QFA_NOTIFY_EMAIL_FROM", "qfa@example.com")
    monkeypatch.setenv("QFA_SMTP_PORT", "2525")
    monkeypatch.setenv("QFA_SMTP_TLS", "false")

    result = CliRunner().invoke(
        cli.app,
        [
            "daemon",
            "run",
            "--once",
            "--notify-email-to",
            "ops@example.com,pm@example.com",
            "--db",
            str(tmp_path / "qfa.sqlite3"),
        ],
    )

    assert result.exit_code == 0
    notifier = CapturingDaemon.configs[-1].notifier
    assert notifier is not None
    assert notifier.config.recipients == ("ops@example.com", "pm@example.com")
    assert notifier.config.sender == "qfa@example.com"
    assert notifier.config.smtp_host == "smtp.example.com"
    assert notifier.config.smtp_port == 2525
    assert notifier.config.use_tls is False


def test_daemon_run_accepts_single_smtp_url_for_email_notifications(tmp_path):
    result = CliRunner().invoke(
        cli.app,
        [
            "daemon",
            "run",
            "--once",
            "--notify-email-to",
            "ops@example.com",
            "--notify-email-smtp-url",
            "smtps://qfa%40example.com:app-pass@smtp.example.com?from=alerts@example.com",
            "--db",
            str(tmp_path / "qfa.sqlite3"),
        ],
    )

    assert result.exit_code == 0
    notifier = CapturingDaemon.configs[-1].notifier
    assert notifier is not None
    assert notifier.config.recipients == ("ops@example.com",)
    assert notifier.config.sender == "alerts@example.com"
    assert notifier.config.smtp_host == "smtp.example.com"
    assert notifier.config.smtp_port == 465
    assert notifier.config.smtp_username == "qfa@example.com"
    assert notifier.config.smtp_password == "app-pass"
    assert notifier.config.use_tls is False
    assert notifier.config.use_ssl is True


def test_daemon_run_accepts_env_smtp_url_and_recipient_for_email_notifications(monkeypatch, tmp_path):
    monkeypatch.setenv("QFA_NOTIFY_EMAIL_TO", "ops@example.com")
    monkeypatch.setenv("QFA_NOTIFY_EMAIL_SMTP_URL", "smtp://qfa@example.com:app-pass@smtp.example.com:2525")

    result = CliRunner().invoke(
        cli.app,
        [
            "daemon",
            "run",
            "--once",
            "--db",
            str(tmp_path / "qfa.sqlite3"),
        ],
    )

    assert result.exit_code == 0
    notifier = CapturingDaemon.configs[-1].notifier
    assert notifier is not None
    assert notifier.config.sender == "qfa@example.com"
    assert notifier.config.smtp_port == 2525
    assert notifier.config.use_tls is True
    assert notifier.config.use_ssl is False


def test_daemon_run_rejects_incomplete_email_notification_configuration(monkeypatch, tmp_path):
    monkeypatch.delenv("QFA_SMTP_HOST", raising=False)
    monkeypatch.delenv("QFA_NOTIFY_EMAIL_FROM", raising=False)
    monkeypatch.delenv("QFA_SMTP_USERNAME", raising=False)

    result = CliRunner().invoke(
        cli.app,
        [
            "daemon",
            "run",
            "--once",
            "--notify-email-to",
            "ops@example.com",
            "--db",
            str(tmp_path / "qfa.sqlite3"),
        ],
    )

    assert result.exit_code == 2
    assert CapturingDaemon.configs == []
    assert "Email notifications require either --notify-email-smtp-url" in result.output


def test_daemon_run_accepts_report_only_orphan_position_guard(tmp_path):
    result = CliRunner().invoke(
        cli.app,
        [
            "daemon",
            "run",
            "--once",
            "--orphan-position-mode",
            "report",
            "--orphan-min-notional",
            "25",
            "--db",
            str(tmp_path / "qfa.sqlite3"),
        ],
    )

    assert result.exit_code == 0
    config = CapturingDaemon.configs[-1]
    assert config.orphan_position_mode == "report"
    assert config.orphan_min_notional == 25.0


def test_daemon_run_blocks_live_orphan_position_liquidation(monkeypatch, tmp_path):
    monkeypatch.setenv("ALPACA_PAPER", "false")

    result = CliRunner().invoke(
        cli.app,
        [
            "daemon",
            "run",
            "--submit-orders",
            "--allow-live-brokerage",
            "--orphan-position-mode",
            "liquidate",
            "--once",
            "--db",
            str(tmp_path / "qfa.sqlite3"),
        ],
    )

    assert result.exit_code != 0
    assert CapturingDaemon.configs == []
    assert "Refusing live orphan-position liquidation" in result.output


def test_daemon_status_reports_last_recorded_heartbeat(tmp_path):
    db_path = tmp_path / "qfa.sqlite3"
    Store(db_path).save_daemon_status(
        {
            "pid": 123,
            "mode": "simulation",
            "paper": True,
            "status": "ok",
            "last_tick_started_at": "2026-06-29T19:00:00Z",
            "last_tick_finished_at": "2026-06-29T19:00:01Z",
            "next_tick_at": "2026-06-29T19:05:01Z",
            "last_error_type": None,
            "last_error_message": None,
        }
    )

    result = CliRunner().invoke(cli.app, ["daemon", "status", "--db", str(db_path)])

    assert result.exit_code == 0
    assert '"status": "ok"' in result.output
    assert '"mode": "simulation"' in result.output


def test_daemon_status_exits_nonzero_without_heartbeat(tmp_path):
    result = CliRunner().invoke(cli.app, ["daemon", "status", "--db", str(tmp_path / "qfa.sqlite3")])

    assert result.exit_code == 1
    assert "No daemon status has been recorded" in result.output


def test_daemon_status_exits_nonzero_when_heartbeat_is_stale(tmp_path):
    db_path = tmp_path / "qfa.sqlite3"
    store = Store(db_path)
    store.save_daemon_status(
        {
            "pid": 123,
            "mode": "simulation",
            "paper": True,
            "status": "ok",
            "last_tick_started_at": "2026-06-29T19:00:00Z",
            "last_tick_finished_at": "2026-06-29T19:00:01Z",
            "next_tick_at": None,
            "last_error_type": None,
            "last_error_message": None,
        }
    )
    store.conn.execute("UPDATE daemon_status SET updated_at = '2000-01-01 00:00:00'")
    store.conn.commit()

    result = CliRunner().invoke(
        cli.app, ["daemon", "status", "--max-age-seconds", "1", "--db", str(db_path)]
    )

    assert result.exit_code == 1
    assert '"status": "stale"' in result.output


def test_daemon_health_reports_log_entries_and_stale_status(tmp_path):
    db_path = tmp_path / "qfa.sqlite3"
    health_log = tmp_path / "health.jsonl"
    store = Store(db_path)
    store.save_daemon_status(
        {
            "pid": 123,
            "mode": "simulation",
            "paper": True,
            "status": "ok",
            "last_tick_started_at": "2026-06-29T19:00:00Z",
            "last_tick_finished_at": "2026-06-29T19:00:01Z",
            "next_tick_at": None,
            "last_error_type": None,
            "last_error_message": None,
        }
    )
    store.conn.execute("UPDATE daemon_status SET updated_at = '2000-01-01 00:00:00'")
    store.conn.commit()
    health_log.write_text(
        '{"event":"daemon_tick","status":"ok","alpha_signal_status":{"active_model_count":1}}\n'
    )

    result = CliRunner().invoke(
        cli.app,
        [
            "daemon",
            "health",
            "--max-age-seconds",
            "1",
            "--health-log",
            str(health_log),
            "--db",
            str(db_path),
        ],
    )

    assert result.exit_code == 1
    assert '"healthy": false' in result.output
    assert '"status": "stale"' in result.output
    assert '"event": "daemon_tick"' in result.output
    assert '"active_model_count": 1' in result.output


def test_daemon_recover_records_safe_recovery_marker(tmp_path):
    db_path = tmp_path / "qfa.sqlite3"
    health_log = tmp_path / "health.jsonl"
    Store(db_path).save_daemon_status(
        {
            "pid": 123,
            "mode": "submit-orders",
            "paper": True,
            "status": "error",
            "last_tick_started_at": "2026-06-29T19:00:00Z",
            "last_tick_finished_at": "2026-06-29T19:00:01Z",
            "next_tick_at": None,
            "last_error_type": "RuntimeError",
            "last_error_message": "data fetch failed",
        }
    )

    result = CliRunner().invoke(
        cli.app,
        [
            "daemon",
            "recover",
            "--reason",
            "operator_reset",
            "--health-log",
            str(health_log),
            "--db",
            str(db_path),
        ],
    )

    assert result.exit_code == 0
    assert '"recovered": true' in result.output
    assert '"safe_mode": "simulation/no-submit"' in result.output
    status = Store(db_path).get_daemon_status()
    assert status is not None
    assert status["status"] == "recovered"
    assert status["last_error_message"] == "operator_reset"
    assert '"event": "daemon_recovery"' in health_log.read_text()


def test_daemon_status_exits_nonzero_for_error_heartbeat(tmp_path):
    db_path = tmp_path / "qfa.sqlite3"
    Store(db_path).save_daemon_status(
        {
            "pid": 123,
            "mode": "simulation",
            "paper": True,
            "status": "error",
            "last_tick_started_at": "2026-06-29T19:00:00Z",
            "last_tick_finished_at": "2026-06-29T19:00:01Z",
            "next_tick_at": None,
            "last_error_type": "RuntimeError",
            "last_error_message": "data fetch failed",
        }
    )

    result = CliRunner().invoke(cli.app, ["daemon", "status", "--db", str(db_path)])

    assert result.exit_code == 1
    assert '"status": "error"' in result.output
    assert '"last_error_type": "RuntimeError"' in result.output


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
