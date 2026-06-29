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
        target_values: dict[str, float] = {}
        target_model_names: dict[str, list[str]] = {}
        for model in models:
            prices = self.alpaca.get_bars(
                model["symbols"],
                start=start.to_pydatetime(),
                end=now.to_pydatetime(),
                asset_class=model.get("asset_class", "equity"),
            )
            context = AlphaContext(symbols=model["symbols"], prices=prices, as_of=now)
            raw = load_alpha_function(model["model_path"])(context) or {}
            weights = normalize_weights(raw, model["symbols"])
            sleeve_notional = equity * float(model["allocation"])
            for symbol, weight in weights.items():
                target_values[symbol] = target_values.get(symbol, 0.0) + (sleeve_notional * weight)
                target_model_names.setdefault(symbol, []).append(model["name"])

        symbols = list(target_values)
        current_values = self.alpaca.position_market_values(symbols)
        open_order_values = self.alpaca.open_order_notional_values(symbols)
        open_order_sides = self.alpaca.open_order_sides(symbols)
        for symbol, target_notional in target_values.items():
            current_notional = current_values.get(symbol, 0.0) + open_order_values.get(symbol, 0.0)
            delta_notional = target_notional - current_notional
            notional = abs(delta_notional)
            if notional < 1.0:
                continue
            side = "buy" if delta_notional >= 0 else "sell"
            pending_sides = open_order_sides.get(symbol, set())
            opposite_side = "sell" if side == "buy" else "buy"
            response = {"dry_run": True, "symbol": symbol, "side": side, "notional": notional}
            if opposite_side in pending_sides:
                response = {
                    "status": "skipped",
                    "reason": "conflicting_open_order",
                    "symbol": symbol,
                    "side": side,
                    "notional": notional,
                    "open_order_sides": sorted(pending_sides),
                }
            elif side in pending_sides:
                response = {
                    "status": "skipped",
                    "reason": "pending_same_side_order",
                    "symbol": symbol,
                    "side": side,
                    "notional": notional,
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
                    try:
                        response = self.alpaca.submit_notional_order(symbol, side, notional)
                    except Exception as exc:  # noqa: BLE001 - broker failures must not stop daemon
                        response = {
                            "status": "error",
                            "error_type": type(exc).__name__,
                            "message": str(exc),
                            "symbol": symbol,
                            "side": side,
                            "notional": notional,
                        }
            event = {
                "model_name": ",".join(target_model_names.get(symbol, [])),
                "symbol": symbol,
                "side": side,
                "notional": notional,
                "dry_run": self.config.dry_run,
                "response": response,
            }
            self.store.save_trade_event(event)
            events.append(event)
        return events
