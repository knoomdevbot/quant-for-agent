import json
from pathlib import Path

from typer.testing import CliRunner

from quant_for_agent import cli
from quant_for_agent.universe import UniverseConfig, build_equity_universe


def test_build_equity_universe_filters_common_stocks_point_in_time():
    root = Path(__file__).resolve().parents[1]

    result = build_equity_universe(
        UniverseConfig(
            as_of="2024-01-02",
            security_master_csv=str(root / "tests" / "fixtures" / "security_master.csv"),
            exchanges=["NASDAQ", "NYSE"],
        )
    )

    assert result["symbols"] == ["AAPL", "MSFT"]
    assert result["point_in_time_universe"] is True
    diagnostics = result["diagnostics"]
    assert diagnostics["selected_count"] == 2
    assert diagnostics["excluded_by_reason"]["delisted_before_as_of"] == 1
    assert diagnostics["excluded_by_reason"]["not_yet_listed"] == 1
    assert diagnostics["excluded_by_reason"]["non_common_stock:etf"] == 1
    assert diagnostics["excluded_by_reason"]["non_common_stock:adr"] == 1
    assert diagnostics["excluded_by_reason"]["unknown_security_type"] == 1
    assert diagnostics["warnings"] == []


def test_universe_equities_cli_returns_symbols_and_diagnostics():
    root = Path(__file__).resolve().parents[1]
    result = CliRunner().invoke(
        cli.app,
        [
            "universe",
            "equities",
            "--security-master-csv",
            str(root / "tests" / "fixtures" / "security_master.csv"),
            "--as-of",
            "2024-01-02",
            "--exchange",
            "NASDAQ",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["symbols"] == ["AAPL", "MSFT"]
    assert payload["universe_spec"]["provider"] == "csv_security_master"
    assert payload["diagnostics"]["excluded_by_reason"]["exchange_filter"] == 3
