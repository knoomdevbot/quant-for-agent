import json

import pandas as pd

from quant_for_agent.daemon import DaemonConfig, TradingDaemon
from quant_for_agent.storage import Store


class FakeAlpacaGateway:
    def account_equity(self):
        return 1000.0

    def get_bars(self, symbols, start, end):
        return pd.DataFrame(
            [
                {
                    "timestamp": pd.Timestamp("2024-01-01"),
                    "symbol": symbol,
                    "open": 100.0,
                    "high": 101.0,
                    "low": 99.0,
                    "close": 100.0,
                    "volume": 1000,
                }
                for symbol in symbols
            ]
        )

    def submit_notional_order(self, symbol, side, notional):
        if symbol == "LLY":
            raise RuntimeError("fractional orders cannot be sold short")
        return {"id": "accepted-order", "symbol": symbol, "side": side, "notional": notional}


def test_daemon_records_order_errors_and_continues_processing_symbols(tmp_path):
    model_path = tmp_path / "negative_weight_model.py"
    model_path.write_text(
        "def generate_signals(context):\n"
        "    return {'LLY': -0.5, 'MSFT': 0.5}\n",
        encoding="utf-8",
    )
    store = Store(tmp_path / "qfa.sqlite3")
    store.upsert_model("risk_model", str(model_path), 1.0, ["LLY", "MSFT"])

    events = TradingDaemon(
        store,
        FakeAlpacaGateway(),
        DaemonConfig(dry_run=False, once=True),
    ).tick()

    assert len(events) == 2
    rejected, accepted = events
    assert rejected["symbol"] == "LLY"
    assert rejected["side"] == "sell"
    assert rejected["response"] == {
        "status": "error",
        "error_type": "RuntimeError",
        "message": "fractional orders cannot be sold short",
        "symbol": "LLY",
        "side": "sell",
        "notional": 500.0,
    }
    assert accepted["symbol"] == "MSFT"
    assert accepted["response"]["id"] == "accepted-order"

    rows = store.conn.execute(
        "SELECT symbol, dry_run, response_json FROM trade_events ORDER BY id"
    ).fetchall()
    assert [row["symbol"] for row in rows] == ["LLY", "MSFT"]
    assert rows[0]["dry_run"] == 0
    assert json.loads(rows[0]["response_json"])["status"] == "error"
