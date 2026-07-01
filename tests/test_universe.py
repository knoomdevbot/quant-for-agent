import json
from pathlib import Path

from typer.testing import CliRunner

from quant_for_agent import cli
from quant_for_agent.universe import UniverseConfig, build_equity_universe, load_security_master_csv


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


def test_partial_date_coverage_is_warned_as_not_point_in_time(tmp_path):
    csv_path = tmp_path / "partial_security_master.csv"
    csv_path.write_text(
        "symbol,exchange,security_type,listing_date\n"
        "AAPL,NASDAQ,common_stock,1980-12-12\n"
        "MSFT,NASDAQ,common_stock,1986-03-13\n"
    )

    result = build_equity_universe(
        UniverseConfig(as_of="2024-01-02", security_master_csv=str(csv_path))
    )

    assert result["symbols"] == ["AAPL", "MSFT"]
    assert result["point_in_time_universe"] is False
    assert "both listing_date and delisting_date" in result["diagnostics"]["warnings"][0]


def test_blank_symbols_are_reported_as_exclusions(tmp_path):
    csv_path = tmp_path / "blank_symbol_security_master.csv"
    csv_path.write_text(
        "symbol,exchange,security_type,listing_date,delisting_date\n"
        "AAPL,NASDAQ,common_stock,1980-12-12,\n"
        ",NASDAQ,common_stock,1980-12-12,\n"
    )

    result = build_equity_universe(
        UniverseConfig(as_of="2024-01-02", security_master_csv=str(csv_path))
    )

    assert result["symbols"] == ["AAPL"]
    assert result["diagnostics"]["excluded_by_reason"]["missing_symbol"] == 1
    assert load_security_master_csv(csv_path)["symbol"].tolist() == ["AAPL", ""]
