import sqlite3
from pathlib import Path

import pytest

from quant_for_agent.backtest import BacktestConfig, run_backtest
from quant_for_agent.data import load_price_csv
from quant_for_agent.storage import Store


def test_run_backtest_calculates_metrics_and_store_roundtrip(tmp_path):
    root = Path(__file__).resolve().parents[1]
    prices = load_price_csv(root / "tests" / "fixtures" / "prices.csv")
    result = run_backtest(
        BacktestConfig(
            model_path=str(root / "examples" / "momentum_alpha.py"),
            symbols=["AAPL", "MSFT"],
            start="2024-01-01",
            end="2024-01-04",
            initial_cash=100000,
        ),
        prices,
    )
    assert result["metrics"]["final_equity"] > 100000
    assert "sharpe" in result["metrics"]

    store = Store(tmp_path / "qfa.sqlite3")
    run_id = store.save_backtest(result)
    saved = store.get_backtest(run_id)
    assert saved is not None
    assert saved["metrics"]["final_equity"] == result["metrics"]["final_equity"]
    assert saved["asset_class"] == "equity"


def test_crypto_backtest_records_asset_bucket_crypto_label_and_fee_model(tmp_path):
    root = Path(__file__).resolve().parents[1]
    prices = load_price_csv(root / "tests" / "fixtures" / "prices.csv")
    prices["symbol"] = prices["symbol"].replace({"AAPL": "BTC/USD", "MSFT": "ETH/USD"})

    result = run_backtest(
        BacktestConfig(
            model_path=str(root / "examples" / "momentum_alpha.py"),
            symbols=["BTC/USD", "ETH/USD"],
            start="2024-01-01",
            end="2024-01-04",
            initial_cash=100000,
            asset_class="crypto",
            fee_maker_bps=0.0,
            fee_taker_bps=25.0,
            fill_mix="taker",
        ),
        prices,
    )

    assert result["asset_class"] == "crypto"
    assert result["asset_bucket"] == "crypto"
    assert result["crypto_label"] is True
    assert result["fee_model"] == {
        "maker_bps": 0.0,
        "taker_bps": 25.0,
        "fill_mix": "taker",
        "effective_bps": 25.0,
    }
    assert result["metrics"]["total_fees"] > 0

    store = Store(tmp_path / "qfa.sqlite3")
    run_id = store.save_backtest(result)
    saved = store.get_backtest(run_id)
    assert saved is not None
    assert saved["asset_class"] == "crypto"
    assert saved["asset_bucket"] == "crypto"
    assert saved["crypto_label"] is True
    assert saved["fee_model"] == result["fee_model"]


def test_crypto_fee_model_reduces_equity_by_turnover_costs():
    root = Path(__file__).resolve().parents[1]
    prices = load_price_csv(root / "tests" / "fixtures" / "prices.csv")
    prices["symbol"] = prices["symbol"].replace({"AAPL": "BTC/USD", "MSFT": "ETH/USD"})

    no_fee = run_backtest(
        BacktestConfig(
            model_path=str(root / "examples" / "momentum_alpha.py"),
            symbols=["BTC/USD", "ETH/USD"],
            start="2024-01-01",
            end="2024-01-04",
            initial_cash=100000,
            asset_class="crypto",
        ),
        prices,
    )
    with_fee = run_backtest(
        BacktestConfig(
            model_path=str(root / "examples" / "momentum_alpha.py"),
            symbols=["BTC/USD", "ETH/USD"],
            start="2024-01-01",
            end="2024-01-04",
            initial_cash=100000,
            asset_class="crypto",
            fee_maker_bps=0.0,
            fee_taker_bps=25.0,
            fill_mix="taker",
        ),
        prices,
    )

    assert with_fee["metrics"]["total_fees"] > 0
    assert with_fee["metrics"]["final_equity"] < no_fee["metrics"]["final_equity"]


@pytest.mark.parametrize(
    ("fee_maker_bps", "fee_taker_bps", "fill_mix", "error"),
    [
        (-1.0, 25.0, "taker", "finite and non-negative"),
        (0.0, float("inf"), "taker", "finite and non-negative"),
        (0.0, 25.0, "auction", "Unsupported fill_mix"),
    ],
)
def test_crypto_fee_model_rejects_invalid_assumptions(
    fee_maker_bps, fee_taker_bps, fill_mix, error
):
    root = Path(__file__).resolve().parents[1]
    prices = load_price_csv(root / "tests" / "fixtures" / "prices.csv")

    with pytest.raises(ValueError, match=error):
        run_backtest(
            BacktestConfig(
                model_path=str(root / "examples" / "momentum_alpha.py"),
                symbols=["AAPL", "MSFT"],
                start="2024-01-01",
                end="2024-01-04",
                asset_class="crypto",
                fee_maker_bps=fee_maker_bps,
                fee_taker_bps=fee_taker_bps,
                fill_mix=fill_mix,
            ),
            prices,
        )


def test_model_registry_upsert_and_remove(tmp_path):
    store = Store(tmp_path / "qfa.sqlite3")
    store.upsert_model("momo", "/tmp/model.py", 0.25, ["AAPL"])
    models = store.list_models()
    assert models[0]["name"] == "momo"
    assert models[0]["allocation"] == 0.25
    assert models[0]["asset_class"] == "equity"
    store.remove_model("momo")
    assert store.list_models() == []


def test_model_registry_persists_crypto_asset_class(tmp_path):
    store = Store(tmp_path / "qfa.sqlite3")

    store.upsert_model("crypto-momo", "/tmp/model.py", 0.05, ["BTC/USD"], asset_class="crypto")

    models = store.list_models()
    assert models[0]["name"] == "crypto-momo"
    assert models[0]["symbols"] == ["BTC/USD"]
    assert models[0]["asset_class"] == "crypto"
    assert models[0]["asset_bucket"] == "crypto"


def test_model_registry_can_filter_by_asset_class(tmp_path):
    store = Store(tmp_path / "qfa.sqlite3")
    store.upsert_model("equity-momo", "/tmp/equity.py", 0.10, ["AAPL"], asset_class="equity")
    store.upsert_model("crypto-momo", "/tmp/crypto.py", 0.05, ["BTC/USD"], asset_class="crypto")

    assert [model["name"] for model in store.list_models(asset_class="crypto")] == ["crypto-momo"]
    assert [model["name"] for model in store.list_models(asset_class="equity")] == ["equity-momo"]


def test_model_registry_migration_backfills_crypto_asset_bucket(tmp_path):
    db_path = tmp_path / "qfa.sqlite3"
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE alpha_models (
          name TEXT PRIMARY KEY,
          model_path TEXT NOT NULL,
          allocation REAL NOT NULL CHECK (allocation >= 0 AND allocation <= 1),
          symbols TEXT NOT NULL,
          asset_class TEXT NOT NULL DEFAULT 'equity',
          active INTEGER NOT NULL DEFAULT 1,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    conn.execute(
        "INSERT INTO alpha_models (name, model_path, allocation, symbols, asset_class) VALUES (?, ?, ?, ?, ?)",
        ("crypto-momo", "/tmp/model.py", 0.05, '["BTC/USD"]', "crypto"),
    )
    conn.commit()
    conn.close()

    models = Store(db_path).list_models()

    assert models[0]["asset_class"] == "crypto"
    assert models[0]["asset_bucket"] == "crypto"
