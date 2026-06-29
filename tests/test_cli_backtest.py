import json
from pathlib import Path

from typer.testing import CliRunner

from quant_for_agent import cli


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
    assert payload["metrics"]["total_fees"] > 0
