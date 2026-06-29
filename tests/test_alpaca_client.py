from __future__ import annotations

import pandas as pd

from quant_for_agent.alpaca_client import AlpacaGateway
from quant_for_agent.config import AlpacaConfig


def test_alpaca_config_reads_data_feed_from_env(monkeypatch):
    monkeypatch.setenv("ALPACA_API_KEY", "paper-key")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "paper-secret")
    monkeypatch.setenv("ALPACA_DATA_FEED", "iex")

    config = AlpacaConfig.from_env()

    assert config.data_feed == "iex"


def test_get_bars_passes_configured_data_feed_to_alpaca_request():
    from alpaca.data.enums import DataFeed

    class FakeBarsResponse:
        df = pd.DataFrame(
            [
                {
                    "timestamp": pd.Timestamp("2024-01-02"),
                    "symbol": "AAPL",
                    "open": 100.0,
                    "high": 101.0,
                    "low": 99.0,
                    "close": 100.5,
                    "volume": 12345,
                }
            ]
        )

    class FakeDataClient:
        request = None

        def get_stock_bars(self, request):
            self.request = request
            return FakeBarsResponse()

    gateway = object.__new__(AlpacaGateway)
    gateway.config = AlpacaConfig("paper-key", "paper-secret", data_feed="iex")
    gateway.data_client = FakeDataClient()

    bars = gateway.get_bars(["AAPL"], "2024-01-01", "2024-01-03")

    assert gateway.data_client.request.feed == DataFeed.IEX
    assert list(bars["symbol"]) == ["AAPL"]


def test_get_bars_routes_crypto_asset_class_to_crypto_data_client():
    class FakeBarsResponse:
        df = pd.DataFrame(
            [
                {
                    "timestamp": pd.Timestamp("2024-01-02"),
                    "symbol": "BTC/USD",
                    "open": 43000.0,
                    "high": 44000.0,
                    "low": 42000.0,
                    "close": 43500.0,
                    "volume": 12.5,
                }
            ]
        )

    class FakeCryptoDataClient:
        request = None

        def get_crypto_bars(self, request):
            self.request = request
            return FakeBarsResponse()

    gateway = object.__new__(AlpacaGateway)
    gateway.config = AlpacaConfig("paper-key", "paper-secret", data_feed="iex")
    gateway.crypto_data_client = FakeCryptoDataClient()

    bars = gateway.get_bars(["BTC/USD"], "2024-01-01", "2024-01-03", asset_class="crypto")

    assert gateway.crypto_data_client.request.symbol_or_symbols == ["BTC/USD"]
    assert not hasattr(gateway.crypto_data_client.request, "feed")
    assert list(bars.columns) == ["timestamp", "symbol", "open", "high", "low", "close", "volume"]
    assert list(bars["symbol"]) == ["BTC/USD"]


def test_get_bars_rejects_unknown_asset_class():
    gateway = object.__new__(AlpacaGateway)
    gateway.config = AlpacaConfig("paper-key", "paper-secret")

    try:
        gateway.get_bars(["AAPL"], "2024-01-01", "2024-01-03", asset_class="futures")
    except ValueError as exc:
        assert "Unsupported asset_class" in str(exc)
    else:  # pragma: no cover - defensive; this test should fail if no exception is raised
        raise AssertionError("expected unsupported asset_class to fail")


def test_alpaca_gateway_uses_gtc_time_in_force_for_crypto_orders():
    submitted = []

    class FakeTradingClient:
        def submit_order(self, order):
            submitted.append(order)
            return {"id": "order"}

    gateway = object.__new__(AlpacaGateway)
    gateway.trading_client = FakeTradingClient()

    response = gateway.submit_notional_order("BTC/USD", "buy", 25.0, asset_class="crypto")

    assert response == {"id": "order"}
    order = submitted[0]
    assert order.symbol == "BTC/USD"
    assert float(order.notional) == 25.0
    assert getattr(order.time_in_force, "value", order.time_in_force) == "gtc"


def test_alpaca_gateway_rejects_crypto_order_without_slash_symbol():
    gateway = object.__new__(AlpacaGateway)

    try:
        gateway.submit_notional_order("BTCUSD", "buy", 25.0, asset_class="crypto")
    except ValueError as exc:
        assert "slash-delimited" in str(exc)
    else:  # pragma: no cover - defensive; this test should fail if no exception is raised
        raise AssertionError("expected unsupported crypto symbol to fail")


def test_alpaca_gateway_rejects_malformed_crypto_bar_symbols():
    gateway = object.__new__(AlpacaGateway)
    gateway.config = AlpacaConfig("paper-key", "paper-secret")

    for symbol in ["BTCUSD", "BTC/", "/USD", "BTC/USD/EXTRA", "btc/usd"]:
        try:
            gateway.get_bars([symbol], "2024-01-01", "2024-01-03", asset_class="crypto")
        except ValueError as exc:
            assert "BASE/QUOTE" in str(exc)
        else:  # pragma: no cover - defensive; this test should fail if no exception is raised
            raise AssertionError(f"expected malformed crypto symbol {symbol} to fail")
