from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from .config import AlpacaConfig


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _position_unit_prices(positions: Any, symbols: set[str]) -> dict[str, float]:
    prices: dict[str, float] = {}
    for position in positions:
        symbol = getattr(position, "symbol", None)
        if symbol not in symbols:
            continue
        qty = _optional_float(getattr(position, "qty", None))
        market_value = _optional_float(getattr(position, "market_value", None))
        if qty and market_value is not None:
            prices[str(symbol)] = abs(market_value) / abs(qty)
    return prices


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

    def _open_orders(self):
        from alpaca.trading.enums import QueryOrderStatus
        from alpaca.trading.requests import GetOrdersRequest

        return self.trading_client.get_orders(filter=GetOrdersRequest(status=QueryOrderStatus.OPEN))

    def open_order_sides(self, symbols: list[str]) -> dict[str, set[str]]:
        allowed = set(symbols)
        sides: dict[str, set[str]] = {symbol: set() for symbol in symbols}
        for order in self._open_orders():
            symbol = getattr(order, "symbol", None)
            if symbol not in allowed:
                continue
            side = str(getattr(order, "side", "")).lower()
            if side.endswith("buy"):
                sides[str(symbol)].add("buy")
            elif side.endswith("sell"):
                sides[str(symbol)].add("sell")
        return sides

    def open_order_notional_values(self, symbols: list[str]) -> dict[str, float]:
        allowed = set(symbols)
        values: dict[str, float] = {symbol: 0.0 for symbol in symbols}
        position_prices: dict[str, float] | None = None
        for order in self._open_orders():
            symbol = getattr(order, "symbol", None)
            if symbol not in allowed:
                continue
            notional = getattr(order, "notional", None)
            qty = _optional_float(getattr(order, "qty", None))
            filled_qty = _optional_float(getattr(order, "filled_qty", None)) or 0.0
            remaining_qty = max(qty - filled_qty, 0.0) if qty is not None else None
            if notional is None:
                price = _optional_float(getattr(order, "limit_price", None))
                if price is None and remaining_qty is not None:
                    if position_prices is None:
                        position_prices = _position_unit_prices(
                            self.trading_client.get_all_positions(), allowed
                        )
                    price = position_prices.get(str(symbol))
                if remaining_qty is None or price is None:
                    continue
                signed_notional = remaining_qty * price
            else:
                signed_notional = float(notional)
                if remaining_qty is not None and qty and qty > 0:
                    signed_notional *= remaining_qty / qty
            side = getattr(order, "side", "")
            if str(side).lower().endswith("sell"):
                signed_notional *= -1.0
            values[str(symbol)] += signed_notional
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
