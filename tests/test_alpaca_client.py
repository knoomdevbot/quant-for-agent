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
