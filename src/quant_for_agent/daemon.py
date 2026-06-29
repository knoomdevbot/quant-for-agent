from __future__ import annotations

import time
from dataclasses import dataclass

from .alpha import AlphaContext, load_alpha_function, normalize_weights
from .alpaca_client import AlpacaGateway
from .storage import Store


# Alpaca converts notional sell orders to fractional share quantities at submission time.
# Keep a small liquidation buffer so price/availability drift does not oversell.
SELL_NOTIONAL_POSITION_BUFFER = 0.995
NEAR_FULL_POSITION_SELL_THRESHOLD = 0.95


@dataclass(frozen=True)
class DaemonConfig:
    interval_seconds: int = 300
    dry_run: bool = True
    once: bool = False
    lookback_days: int = 90


class TradingDaemon:
    def __init__(self, store: Store, alpaca: AlpacaGateway, config: DaemonConfig):
        self.store = store
        self.alpaca = alpaca
        self.config = config

    def run(self) -> None:
        while True:
            self.tick()
            if self.config.once:
                return
            time.sleep(self.config.interval_seconds)

    def tick(self) -> list[dict]:
        import pandas as pd

        models = self.store.list_models(active_only=True)
        events: list[dict] = []
        if not models:
            return events
        now = pd.Timestamp.utcnow()
        start = now - pd.Timedelta(days=self.config.lookback_days)
        equity = self.alpaca.account_equity()
        symbol_asset_classes: dict[str, set[str]] = {}
        symbol_model_names: dict[str, list[str]] = {}
        for model in models:
            asset_class = model.get("asset_class", "equity")
            for symbol in model["symbols"]:
                symbol_asset_classes.setdefault(symbol, set()).add(asset_class)
                symbol_model_names.setdefault(symbol, []).append(model["name"])
        conflicting_asset_classes = {
            symbol: asset_classes
            for symbol, asset_classes in symbol_asset_classes.items()
            if len(asset_classes) > 1
        }
        target_values: dict[str, float] = {}
        target_model_names: dict[str, list[str]] = {}
        target_asset_classes: dict[str, set[str]] = {}
        for model in models:
            asset_class = model.get("asset_class", "equity")
            symbols = [symbol for symbol in model["symbols"] if symbol not in conflicting_asset_classes]
            if not symbols:
                continue
            prices = self.alpaca.get_bars(
                symbols,
                start=start.to_pydatetime(),
                end=now.to_pydatetime(),
                asset_class=asset_class,
            )
            context = AlphaContext(symbols=symbols, prices=prices, as_of=now)
            raw = load_alpha_function(model["model_path"])(context) or {}
            weights = normalize_weights(raw, symbols)
            sleeve_notional = equity * float(model["allocation"])
            for symbol, weight in weights.items():
                target_values[symbol] = target_values.get(symbol, 0.0) + (sleeve_notional * weight)
                target_model_names.setdefault(symbol, []).append(model["name"])
                target_asset_classes.setdefault(symbol, set()).add(asset_class)

        for symbol, asset_classes in conflicting_asset_classes.items():
            response = {
                "status": "skipped",
                "reason": "conflicting_asset_classes",
                "symbol": symbol,
                "asset_classes": sorted(asset_classes),
            }
            event = {
                "model_name": ",".join(symbol_model_names.get(symbol, [])),
                "symbol": symbol,
                "side": "skip",
                "notional": 0.0,
                "asset_class": "mixed",
                "dry_run": self.config.dry_run,
                "response": response,
            }
            self.store.save_trade_event(event)
            events.append(event)

        symbols = list(target_values)
        current_values = self.alpaca.position_market_values(symbols)
        open_order_values = self.alpaca.open_order_notional_values(symbols)
        open_order_sides = self.alpaca.open_order_sides(symbols)
        for symbol, target_notional in target_values.items():
            asset_classes = target_asset_classes.get(symbol, {"equity"})
            if len(asset_classes) != 1:
                response = {
                    "status": "skipped",
                    "reason": "conflicting_asset_classes",
                    "symbol": symbol,
                    "asset_classes": sorted(asset_classes),
                }
                event = {
                    "model_name": ",".join(target_model_names.get(symbol, [])),
                    "symbol": symbol,
                    "side": "skip",
                    "notional": 0.0,
                    "asset_class": "mixed",
                    "dry_run": self.config.dry_run,
                    "response": response,
                }
                self.store.save_trade_event(event)
                events.append(event)
                continue
            asset_class = next(iter(asset_classes))
            current_notional = current_values.get(symbol, 0.0) + open_order_values.get(symbol, 0.0)
            delta_notional = target_notional - current_notional
            notional = abs(delta_notional)
            if notional < 1.0:
                continue
            side = "buy" if delta_notional >= 0 else "sell"
            pending_sides = open_order_sides.get(symbol, set())
            opposite_side = "sell" if side == "buy" else "buy"
            response = {
                "dry_run": True,
                "symbol": symbol,
                "side": side,
                "notional": notional,
                "asset_class": asset_class,
            }
            if opposite_side in pending_sides:
                response = {
                    "status": "skipped",
                    "reason": "conflicting_open_order",
                    "symbol": symbol,
                    "side": side,
                    "notional": notional,
                    "asset_class": asset_class,
                    "open_order_sides": sorted(pending_sides),
                }
            elif side in pending_sides:
                response = {
                    "status": "skipped",
                    "reason": "pending_same_side_order",
                    "symbol": symbol,
                    "side": side,
                    "notional": notional,
                    "asset_class": asset_class,
                    "open_order_sides": sorted(pending_sides),
                }
            else:
                current_position_notional = current_values.get(symbol, 0.0)
                if (
                    side == "sell"
                    and current_position_notional > 0
                    and notional >= current_position_notional * NEAR_FULL_POSITION_SELL_THRESHOLD
                ):
                    notional = min(notional, current_position_notional * SELL_NOTIONAL_POSITION_BUFFER)
                    response["notional"] = notional
                if not self.config.dry_run:
                    if asset_class == "equity" and not self.alpaca.is_market_open():
                        response = {
                            "status": "skipped",
                            "reason": "market_closed",
                            "symbol": symbol,
                            "side": side,
                            "notional": notional,
                            "asset_class": asset_class,
                        }
                    else:
                        try:
                            response = self.alpaca.submit_notional_order(
                                symbol, side, notional, asset_class=asset_class
                            )
                        except Exception as exc:  # noqa: BLE001 - broker failures must not stop daemon
                            response = {
                                "status": "error",
                                "error_type": type(exc).__name__,
                                "message": str(exc),
                                "symbol": symbol,
                                "side": side,
                                "notional": notional,
                                "asset_class": asset_class,
                            }
            event = {
                "model_name": ",".join(target_model_names.get(symbol, [])),
                "symbol": symbol,
                "side": side,
                "notional": notional,
                "asset_class": asset_class,
                "dry_run": self.config.dry_run,
                "response": response,
            }
            self.store.save_trade_event(event)
            events.append(event)
        return events
