from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from .config import AlpacaConfig


class AlpacaGateway:
    def __init__(self, config: AlpacaConfig | None = None):
        self.config = config or AlpacaConfig.from_env()
        try:
            from alpaca.data.historical import StockHistoricalDataClient
            from alpaca.trading.client import TradingClient
        except ImportError as exc:  # pragma: no cover - exercised only when dependency missing
            raise RuntimeError("Install alpaca-py to use Alpaca integration") from exc
        self.data_client = StockHistoricalDataClient(self.config.api_key, self.config.secret_key)
        self.trading_client = TradingClient(
            self.config.api_key, self.config.secret_key, paper=self.config.paper
        )

    def get_bars(
        self, symbols: list[str], start: datetime | str, end: datetime | str, timeframe: str = "1Day"
    ) -> pd.DataFrame:
        from alpaca.data.enums import DataFeed
        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame

        tf = TimeFrame.Day if timeframe in {"1Day", "day", "daily"} else TimeFrame.Minute
        feed = DataFeed(self.config.data_feed) if self.config.data_feed else None
        request = StockBarsRequest(
            symbol_or_symbols=symbols, timeframe=tf, start=start, end=end, feed=feed
        )
        bars = self.data_client.get_stock_bars(request).df.reset_index()
        rename = {"symbol": "symbol", "timestamp": "timestamp"}
        bars = bars.rename(columns=rename)
        return bars[["timestamp", "symbol", "open", "high", "low", "close", "volume"]]

    def account_equity(self) -> float:
        return float(self.trading_client.get_account().equity)

    def position_market_values(self, symbols: list[str]) -> dict[str, float]:
        allowed = set(symbols)
        values: dict[str, float] = {symbol: 0.0 for symbol in symbols}
        for position in self.trading_client.get_all_positions():
            symbol = getattr(position, "symbol", None)
            if symbol not in allowed:
                continue
            values[str(symbol)] = float(getattr(position, "market_value", 0.0) or 0.0)
        return values

    def submit_notional_order(self, symbol: str, side: str, notional: float) -> dict[str, Any]:
        from alpaca.trading.enums import OrderSide, TimeInForce
        from alpaca.trading.requests import MarketOrderRequest

        order = self.trading_client.submit_order(
            MarketOrderRequest(
                symbol=symbol,
                notional=round(float(notional), 2),
                side=OrderSide.BUY if side == "buy" else OrderSide.SELL,
                time_in_force=TimeInForce.DAY,
            )
        )
        return order.model_dump(mode="json") if hasattr(order, "model_dump") else dict(order)
