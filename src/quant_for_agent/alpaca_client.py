from __future__ import annotations

from datetime import datetime
import re
from typing import Any

import pandas as pd

from .config import AlpacaConfig

SUPPORTED_ASSET_CLASSES = {"equity", "crypto"}
CRYPTO_SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]+/[A-Z0-9]+$")


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _normalize_asset_class(asset_class: str) -> str:
    normalized = asset_class.strip().lower()
    if normalized not in SUPPORTED_ASSET_CLASSES:
        supported = ", ".join(sorted(SUPPORTED_ASSET_CLASSES))
        raise ValueError(f"Unsupported asset_class {asset_class!r}; expected one of: {supported}")
    return normalized


def _ohlcv_frame(bars: pd.DataFrame) -> pd.DataFrame:
    bars = bars.rename(columns={"symbol": "symbol", "timestamp": "timestamp"})
    return bars[["timestamp", "symbol", "open", "high", "low", "close", "volume"]]


def _validate_crypto_symbols(symbols: list[str]) -> None:
    invalid = [symbol for symbol in symbols if not CRYPTO_SYMBOL_PATTERN.fullmatch(symbol)]
    if invalid:
        raise ValueError(
            "Crypto symbols must use Alpaca slash-delimited BASE/QUOTE format, "
            f"for example BTC/USD. Invalid: {', '.join(invalid)}"
        )


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
            from alpaca.data.historical import CryptoHistoricalDataClient, StockHistoricalDataClient
            from alpaca.trading.client import TradingClient
        except ImportError as exc:  # pragma: no cover - exercised only when dependency missing
            raise RuntimeError("Install alpaca-py to use Alpaca integration") from exc
        self.data_client = StockHistoricalDataClient(self.config.api_key, self.config.secret_key)
        self.crypto_data_client = CryptoHistoricalDataClient(
            self.config.api_key, self.config.secret_key
        )
        self.trading_client = TradingClient(
            self.config.api_key, self.config.secret_key, paper=self.config.paper
        )

    def get_bars(
        self,
        symbols: list[str],
        start: datetime | str,
        end: datetime | str,
        timeframe: str = "1Day",
        asset_class: str = "equity",
    ) -> pd.DataFrame:
        from alpaca.data.enums import DataFeed
        from alpaca.data.requests import CryptoBarsRequest, StockBarsRequest
        from alpaca.data.timeframe import TimeFrame

        normalized_asset_class = _normalize_asset_class(asset_class)
        tf = TimeFrame.Day if timeframe in {"1Day", "day", "daily"} else TimeFrame.Minute
        if normalized_asset_class == "crypto":
            _validate_crypto_symbols(symbols)
            request = CryptoBarsRequest(
                symbol_or_symbols=symbols, timeframe=tf, start=start, end=end
            )
            bars = self.crypto_data_client.get_crypto_bars(request).df.reset_index()
        else:
            feed = DataFeed(self.config.data_feed) if self.config.data_feed else None
            request = StockBarsRequest(
                symbol_or_symbols=symbols, timeframe=tf, start=start, end=end, feed=feed
            )
            bars = self.data_client.get_stock_bars(request).df.reset_index()
        return _ohlcv_frame(bars)

    def account_equity(self) -> float:
        return float(self.trading_client.get_account().equity)

    def is_market_open(self) -> bool:
        return bool(getattr(self.trading_client.get_clock(), "is_open"))

    def position_market_values(self, symbols: list[str]) -> dict[str, float]:
        allowed = set(symbols)
        values: dict[str, float] = {symbol: 0.0 for symbol in symbols}
        for position in self.trading_client.get_all_positions():
            symbol = getattr(position, "symbol", None)
            if symbol not in allowed:
                continue
            values[str(symbol)] = float(getattr(position, "market_value", 0.0) or 0.0)
        return values

    def all_position_market_values(self) -> dict[str, float]:
        values: dict[str, float] = {}
        for position in self.trading_client.get_all_positions():
            symbol = getattr(position, "symbol", None)
            if symbol is None:
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

    def submit_notional_order(
        self, symbol: str, side: str, notional: float, asset_class: str = "equity"
    ) -> dict[str, Any]:
        from alpaca.trading.enums import OrderSide, TimeInForce
        from alpaca.trading.requests import MarketOrderRequest

        normalized_asset_class = _normalize_asset_class(asset_class)
        if normalized_asset_class == "crypto":
            _validate_crypto_symbols([symbol])
        time_in_force = TimeInForce.GTC if normalized_asset_class == "crypto" else TimeInForce.DAY
        order = self.trading_client.submit_order(
            MarketOrderRequest(
                symbol=symbol,
                notional=round(float(notional), 2),
                side=OrderSide.BUY if side == "buy" else OrderSide.SELL,
                time_in_force=time_in_force,
            )
        )
        return order.model_dump(mode="json") if hasattr(order, "model_dump") else dict(order)
