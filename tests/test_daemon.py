import json
from types import SimpleNamespace

import pandas as pd

from quant_for_agent.alpaca_client import AlpacaGateway
from quant_for_agent.daemon import DaemonConfig, TradingDaemon
from quant_for_agent.storage import Store


class FakeAlpacaGateway:
    def __init__(self, positions=None, open_orders=None, open_order_sides=None):
        self.positions = positions or {}
        self.open_orders = open_orders or {}
        self._open_order_sides = open_order_sides or {}
        self.submitted_orders = []

    def account_equity(self):
        return 1000.0

    def position_market_values(self, symbols):
        return {symbol: self.positions.get(symbol, 0.0) for symbol in symbols}

    def open_order_notional_values(self, symbols):
        return {symbol: self.open_orders.get(symbol, 0.0) for symbol in symbols}

    def open_order_sides(self, symbols):
        return {symbol: set(self._open_order_sides.get(symbol, set())) for symbol in symbols}

    def get_bars(self, symbols, start, end, asset_class="equity"):
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
        self.submitted_orders.append({"symbol": symbol, "side": side, "notional": notional})
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


def test_daemon_submits_only_delta_between_current_and_target_position(tmp_path):
    model_path = tmp_path / "target_weight_model.py"
    model_path.write_text(
        "def generate_signals(context):\n"
        "    return {'AAPL': 0.6, 'MSFT': 0.4}\n",
        encoding="utf-8",
    )
    store = Store(tmp_path / "qfa.sqlite3")
    store.upsert_model("rebalance_model", str(model_path), 1.0, ["AAPL", "MSFT"])
    alpaca = FakeAlpacaGateway(positions={"AAPL": 600.0, "MSFT": 100.0})

    events = TradingDaemon(
        store,
        alpaca,
        DaemonConfig(dry_run=False, once=True),
    ).tick()

    assert len(events) == 1
    assert events[0]["symbol"] == "MSFT"
    assert events[0]["side"] == "buy"
    assert events[0]["notional"] == 300.0
    assert alpaca.submitted_orders == [{"symbol": "MSFT", "side": "buy", "notional": 300.0}]


def test_daemon_rebalances_shared_symbols_against_aggregate_target(tmp_path):
    model_path = tmp_path / "shared_symbol_model.py"
    model_path.write_text(
        "def generate_signals(context):\n"
        "    return {'AAPL': 1.0}\n",
        encoding="utf-8",
    )
    store = Store(tmp_path / "qfa.sqlite3")
    store.upsert_model("core_model", str(model_path), 0.5, ["AAPL"])
    store.upsert_model("satellite_model", str(model_path), 0.5, ["AAPL"])
    alpaca = FakeAlpacaGateway(positions={"AAPL": 1000.0})

    events = TradingDaemon(
        store,
        alpaca,
        DaemonConfig(dry_run=False, once=True),
    ).tick()

    assert events == []
    assert alpaca.submitted_orders == []


def test_daemon_rebalances_against_pending_open_orders(tmp_path):
    model_path = tmp_path / "target_weight_model.py"
    model_path.write_text(
        "def generate_signals(context):\n"
        "    return {'AAPL': 0.6}\n",
        encoding="utf-8",
    )
    store = Store(tmp_path / "qfa.sqlite3")
    store.upsert_model("rebalance_model", str(model_path), 0.6, ["AAPL"])
    alpaca = FakeAlpacaGateway(positions={"AAPL": 400.0}, open_orders={"AAPL": 200.0})

    events = TradingDaemon(
        store,
        alpaca,
        DaemonConfig(dry_run=False, once=True),
    ).tick()

    assert events == []
    assert alpaca.submitted_orders == []


def test_daemon_skips_opposite_side_submission_when_open_order_is_pending(tmp_path):
    model_path = tmp_path / "target_weight_model.py"
    model_path.write_text(
        "def generate_signals(context):\n"
        "    return {'AAPL': 1.0}\n",
        encoding="utf-8",
    )
    store = Store(tmp_path / "qfa.sqlite3")
    store.upsert_model("rebalance_model", str(model_path), 0.4, ["AAPL"])
    alpaca = FakeAlpacaGateway(
        positions={"AAPL": 100.0},
        open_orders={"AAPL": 500.0},
        open_order_sides={"AAPL": {"buy"}},
    )

    events = TradingDaemon(
        store,
        alpaca,
        DaemonConfig(dry_run=False, once=True),
    ).tick()

    assert len(events) == 1
    assert events[0]["symbol"] == "AAPL"
    assert events[0]["side"] == "sell"
    assert events[0]["response"] == {
        "status": "skipped",
        "reason": "conflicting_open_order",
        "symbol": "AAPL",
        "side": "sell",
        "notional": 200.0,
        "open_order_sides": ["buy"],
    }
    assert alpaca.submitted_orders == []


def test_daemon_caps_near_full_position_sell_to_avoid_fractional_availability_rejection(tmp_path):
    model_path = tmp_path / "target_weight_model.py"
    model_path.write_text(
        "def generate_signals(context):\n"
        "    return {'TLT': 0.0}\n",
        encoding="utf-8",
    )
    store = Store(tmp_path / "qfa.sqlite3")
    store.upsert_model("rebalance_model", str(model_path), 1.0, ["TLT"])
    alpaca = FakeAlpacaGateway(positions={"TLT": 3234.4673283})

    events = TradingDaemon(
        store,
        alpaca,
        DaemonConfig(dry_run=False, once=True),
    ).tick()

    assert len(events) == 1
    assert events[0]["symbol"] == "TLT"
    assert events[0]["side"] == "sell"
    assert events[0]["notional"] == 3218.2949916585003
    assert alpaca.submitted_orders == [
        {"symbol": "TLT", "side": "sell", "notional": 3218.2949916585003}
    ]


def test_daemon_skips_duplicate_submission_when_same_side_order_is_pending(tmp_path):
    model_path = tmp_path / "target_weight_model.py"
    model_path.write_text(
        "def generate_signals(context):\n"
        "    return {'TLT': 1.0}\n",
        encoding="utf-8",
    )
    store = Store(tmp_path / "qfa.sqlite3")
    store.upsert_model("rebalance_model", str(model_path), 0.2, ["TLT"])
    alpaca = FakeAlpacaGateway(
        positions={"TLT": 305.0},
        open_orders={"TLT": -100.0},
        open_order_sides={"TLT": {"sell"}},
    )

    events = TradingDaemon(
        store,
        alpaca,
        DaemonConfig(dry_run=False, once=True),
    ).tick()

    assert len(events) == 1
    assert events[0]["symbol"] == "TLT"
    assert events[0]["side"] == "sell"
    assert events[0]["response"] == {
        "status": "skipped",
        "reason": "pending_same_side_order",
        "symbol": "TLT",
        "side": "sell",
        "notional": 5.0,
        "open_order_sides": ["sell"],
    }
    assert alpaca.submitted_orders == []


def test_alpaca_gateway_reports_open_order_sides():
    class FakeTradingClient:
        def get_orders(self, filter=None):
            return [
                SimpleNamespace(symbol="AAPL", side="buy"),
                SimpleNamespace(symbol="AAPL", side="sell"),
                SimpleNamespace(symbol="MSFT", side="sell"),
                SimpleNamespace(symbol="TSLA", side="buy"),
            ]

    gateway = object.__new__(AlpacaGateway)
    gateway.trading_client = FakeTradingClient()

    sides = gateway.open_order_sides(["AAPL", "MSFT"])

    assert sides == {"AAPL": {"buy", "sell"}, "MSFT": {"sell"}}


def test_alpaca_gateway_sums_signed_open_order_notional_values():
    class FakeTradingClient:
        def __init__(self):
            self.filter = None

        def get_orders(self, filter=None):
            self.filter = filter
            return [
                SimpleNamespace(symbol="AAPL", side="buy", notional="100.25"),
                SimpleNamespace(symbol="AAPL", side="sell", notional="40.00"),
                SimpleNamespace(symbol="MSFT", side="sell", notional="15.50"),
                SimpleNamespace(symbol="TSLA", side="buy", notional="999.00"),
            ]

    gateway = object.__new__(AlpacaGateway)
    trading_client = FakeTradingClient()
    gateway.trading_client = trading_client

    values = gateway.open_order_notional_values(["AAPL", "MSFT"])

    assert getattr(trading_client.filter.status, "value", trading_client.filter.status) == "open"
    assert values == {"AAPL": 60.25, "MSFT": -15.5}


def test_alpaca_gateway_counts_only_remaining_open_order_notional():
    class FakeTradingClient:
        def get_orders(self, filter=None):
            return [
                SimpleNamespace(
                    symbol="AAPL", side="buy", notional="100.00", qty="10", filled_qty="4"
                ),
                SimpleNamespace(
                    symbol="AAPL", side="sell", notional=None, qty="3", filled_qty="1", limit_price="20"
                ),
            ]

    gateway = object.__new__(AlpacaGateway)
    gateway.trading_client = FakeTradingClient()

    values = gateway.open_order_notional_values(["AAPL"])

    assert values == {"AAPL": 20.0}


def test_alpaca_gateway_values_qty_only_open_sell_orders_from_position_price():
    class FakeTradingClient:
        def get_orders(self, filter=None):
            return [
                SimpleNamespace(
                    symbol="AAPL", side="sell", notional=None, qty="3", filled_qty="1", limit_price=None
                )
            ]

        def get_all_positions(self):
            return [SimpleNamespace(symbol="AAPL", qty="10", market_value="1500.00")]

    gateway = object.__new__(AlpacaGateway)
    gateway.trading_client = FakeTradingClient()

    values = gateway.open_order_notional_values(["AAPL"])

    assert values == {"AAPL": -300.0}
