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


def test_model_registry_upsert_and_remove(tmp_path):
    store = Store(tmp_path / "qfa.sqlite3")
    store.upsert_model("momo", "/tmp/model.py", 0.25, ["AAPL"])
    models = store.list_models()
    assert models[0]["name"] == "momo"
    assert models[0]["allocation"] == 0.25
    store.remove_model("momo")
    assert store.list_models() == []
