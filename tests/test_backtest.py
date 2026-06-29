from pathlib import Path

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


def test_crypto_backtest_records_asset_bucket_and_crypto_label(tmp_path):
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
        ),
        prices,
    )

    assert result["asset_class"] == "crypto"
    assert result["asset_bucket"] == "crypto"
    assert result["crypto_label"] is True

    store = Store(tmp_path / "qfa.sqlite3")
    run_id = store.save_backtest(result)
    saved = store.get_backtest(run_id)
    assert saved is not None
    assert saved["asset_class"] == "crypto"
    assert saved["asset_bucket"] == "crypto"
    assert saved["crypto_label"] is True


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
