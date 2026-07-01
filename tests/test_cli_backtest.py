import json
from pathlib import Path

from typer.testing import CliRunner

from quant_for_agent import cli
from quant_for_agent.storage import Store


def test_backtest_run_accepts_crypto_fee_model_options(tmp_path):
    root = Path(__file__).resolve().parents[1]
    result = CliRunner().invoke(
        cli.app,
        [
            "backtest",
            "run",
            str(root / "examples" / "momentum_alpha.py"),
            "--symbols",
            "AAPL,MSFT",
            "--start",
            "2024-01-01",
            "--end",
            "2024-01-04",
            "--data-csv",
            str(root / "tests" / "fixtures" / "prices.csv"),
            "--asset-class",
            "crypto",
            "--fee-maker-bps",
            "0",
            "--fee-taker-bps",
            "25",
            "--fill-mix",
            "taker",
            "--db",
            str(tmp_path / "qfa.sqlite3"),
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["asset_class"] == "crypto"
    assert payload["fee_model"] == {
        "maker_bps": 0.0,
        "taker_bps": 25.0,
        "fill_mix": "taker",
        "effective_bps": 25.0,
    }
    assert payload["point_in_time_universe"] is False
    assert payload["universe_spec"]["provider"] == "explicit_symbols"
    assert payload["metrics"]["total_fees"] > 0


def test_models_list_filters_by_asset_class(tmp_path):
    db_path = tmp_path / "qfa.sqlite3"
    store = Store(db_path)
    store.upsert_model("equity", "/tmp/equity.py", 0.10, ["AAPL"], asset_class="equity")
    store.upsert_model("crypto", "/tmp/crypto.py", 0.05, ["BTC/USD"], asset_class="crypto")

    result = CliRunner().invoke(
        cli.app,
        ["models", "list", "--asset-class", "crypto", "--db", str(db_path)],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert [model["name"] for model in payload] == ["crypto"]
    assert payload[0]["asset_bucket"] == "crypto"
