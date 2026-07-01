from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .alpha import AlphaContext, load_alpha_function, normalize_weights
from .alpaca_client import AlpacaGateway
from .health import append_health_log
from .storage import Store


# Alpaca converts notional sell orders to fractional share quantities at submission time.
# Keep a small liquidation buffer so price/availability drift does not oversell.
SELL_NOTIONAL_POSITION_BUFFER = 0.995
NEAR_FULL_POSITION_SELL_THRESHOLD = 0.95


def _format_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _utc_now() -> str:
    return _format_utc(datetime.now(timezone.utc))


@dataclass(frozen=True)
class DaemonConfig:
    interval_seconds: int = 300
    dry_run: bool = True
    once: bool = False
    lookback_days: int = 90
    paper: bool | None = None
    data_feed: str | None = None
    health_log_path: str | None = None
    orphan_position_mode: str = "off"
    orphan_min_notional: float = 1.0


class TradingDaemon:
    def __init__(self, store: Store, alpaca: AlpacaGateway, config: DaemonConfig):
        self.store = store
        self.alpaca = alpaca
        self.config = config
        self._last_signal_status: dict = {}

    def run(self) -> None:
        while True:
            tick_started_at = _utc_now()
            self._save_status(
                status="running",
                last_tick_started_at=tick_started_at,
                last_tick_finished_at=None,
                next_tick_at=None,
            )
            try:
                events = self.tick() or []
            except Exception as exc:
                tick_finished_at = _utc_now()
                self._save_status(
                    status="error",
                    last_tick_started_at=tick_started_at,
                    last_tick_finished_at=tick_finished_at,
                    next_tick_at=None,
                    last_error_type=type(exc).__name__,
                    last_error_message=str(exc),
                )
                self._emit_tick_log(
                    status="error",
                    last_tick_started_at=tick_started_at,
                    last_tick_finished_at=tick_finished_at,
                    next_tick_at=None,
                    trade_event_count=0,
                    last_error_type=type(exc).__name__,
                    last_error_message=self._format_log_error_message(exc),
                )
                raise
            tick_finished_at = _utc_now()
            if self.config.once:
                self._save_status(
                    status="ok",
                    last_tick_started_at=tick_started_at,
                    last_tick_finished_at=tick_finished_at,
                    next_tick_at=None,
                )
                self._emit_tick_log(
                    status="ok",
                    last_tick_started_at=tick_started_at,
                    last_tick_finished_at=tick_finished_at,
                    next_tick_at=None,
                    trade_event_count=len(events),
                )
                return
            next_tick_at = _format_utc(
                datetime.now(timezone.utc) + timedelta(seconds=self.config.interval_seconds)
            )
            self._save_status(
                status="ok",
                last_tick_started_at=tick_started_at,
                last_tick_finished_at=tick_finished_at,
                next_tick_at=next_tick_at,
            )
            self._emit_tick_log(
                status="ok",
                last_tick_started_at=tick_started_at,
                last_tick_finished_at=tick_finished_at,
                next_tick_at=next_tick_at,
                trade_event_count=len(events),
            )
            time.sleep(self.config.interval_seconds)

    def _emit_tick_log(
        self,
        *,
        status: str,
        last_tick_started_at: str | None,
        last_tick_finished_at: str | None,
        next_tick_at: str | None,
        trade_event_count: int,
        last_error_type: str | None = None,
        last_error_message: str | None = None,
    ) -> None:
        payload = {
            "event": "daemon_tick",
            "status": status,
            "mode": "simulation" if self.config.dry_run else "submit-orders",
            "paper": self.config.paper,
            "data_feed": self.config.data_feed,
            "last_tick_started_at": last_tick_started_at,
            "last_tick_finished_at": last_tick_finished_at,
            "next_tick_at": next_tick_at,
            "trade_event_count": trade_event_count,
            "no_order_reason": "no_trade_events" if status == "ok" and trade_event_count == 0 else None,
            "alpha_signal_status": self._last_signal_status,
            "last_error_type": last_error_type,
            "last_error_message": last_error_message,
        }
        try:
            print(json.dumps(payload, sort_keys=True), flush=True)
            append_health_log(self.config.health_log_path, payload)
        except Exception:
            # Tick logging is observability-only. It must not crash the daemon.
            return

    def _format_log_error_message(self, exc: Exception) -> str:
        return " ".join(str(exc).split())[:500]

    def _save_status(
        self,
        *,
        status: str,
        last_tick_started_at: str | None,
        last_tick_finished_at: str | None,
        next_tick_at: str | None,
        last_error_type: str | None = None,
        last_error_message: str | None = None,
    ) -> None:
        try:
            self.store.save_daemon_status(
                {
                    "pid": os.getpid(),
                    "mode": "simulation" if self.config.dry_run else "submit-orders",
                    "paper": self.config.paper,
                    "data_feed": self.config.data_feed,
                    "status": status,
                    "last_tick_started_at": last_tick_started_at,
                    "last_tick_finished_at": last_tick_finished_at,
                    "next_tick_at": next_tick_at,
                    "last_error_type": last_error_type,
                    "last_error_message": last_error_message,
                }
            )
        except Exception:
            # Heartbeat persistence is observability-only. It must not crash the
            # trading loop, especially after a tick may have submitted orders.
            return

    def tick(self) -> list[dict]:
        import pandas as pd

        models = self.store.list_models(active_only=True)
        events: list[dict] = []
        signal_status = {
            "active_model_count": len(models),
            "evaluated_model_count": 0,
            "symbols_evaluated": [],
            "raw_signal_count": 0,
            "normalized_signal_count": 0,
        }
        self._last_signal_status = signal_status
        if not models:
            self._handle_orphan_positions(events=events, active_symbols=set())
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
            signal_status["evaluated_model_count"] += 1
            signal_status["symbols_evaluated"] = sorted(
                set(signal_status["symbols_evaluated"]) | set(symbols)
            )
            signal_status["raw_signal_count"] += sum(
                1 for symbol, weight in raw.items() if symbol in symbols and float(weight or 0.0) != 0.0
            )
            signal_status["normalized_signal_count"] += sum(
                1 for weight in weights.values() if float(weight) != 0.0
            )
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

        self._handle_orphan_positions(
            events=events,
            active_symbols=set(symbol_asset_classes),
        )

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

    def _handle_orphan_positions(self, *, events: list[dict], active_symbols: set[str]) -> None:
        mode = self.config.orphan_position_mode.strip().lower()
        if mode == "off":
            return
        if mode not in {"report", "liquidate"}:
            raise ValueError("orphan_position_mode must be one of: off, report, liquidate")
        all_positions = self.alpaca.all_position_market_values()
        orphan_values = {
            symbol: market_value
            for symbol, market_value in all_positions.items()
            if symbol not in active_symbols and abs(market_value) >= self.config.orphan_min_notional
        }
        if not orphan_values:
            return
        open_order_sides = self.alpaca.open_order_sides(list(orphan_values))
        for symbol in sorted(orphan_values):
            market_value = orphan_values[symbol]
            notional = abs(market_value)
            side = "sell" if market_value > 0 else "buy"
            order_notional = notional * SELL_NOTIONAL_POSITION_BUFFER if side == "sell" else notional
            event_side = "report" if mode == "report" else side
            pending_sides = open_order_sides.get(symbol, set())
            response: dict
            if mode == "report":
                response = {
                    "status": "reported",
                    "reason": "orphan_position",
                    "symbol": symbol,
                    "market_value": market_value,
                    "asset_class": "equity",
                }
            else:
                response = {
                    "dry_run": True,
                    "reason": "orphan_position_liquidation_preview",
                    "symbol": symbol,
                    "side": side,
                    "notional": order_notional,
                    "asset_class": "equity",
                }
                if pending_sides:
                    response = {
                        "status": "skipped",
                        "reason": "orphan_open_order_pending",
                        "symbol": symbol,
                        "side": side,
                        "notional": notional,
                        "asset_class": "equity",
                        "open_order_sides": sorted(pending_sides),
                    }
                elif not self.config.dry_run:
                    if self.config.paper is not True:
                        response = {
                            "status": "skipped",
                            "reason": "paper_orphan_liquidation_required",
                            "symbol": symbol,
                            "side": side,
                            "notional": notional,
                            "asset_class": "equity",
                        }
                    elif not self.alpaca.is_market_open():
                        response = {
                            "status": "skipped",
                            "reason": "market_closed",
                            "symbol": symbol,
                            "side": side,
                            "notional": order_notional,
                            "asset_class": "equity",
                        }
                    else:
                        try:
                            response = self.alpaca.submit_notional_order(
                                symbol, side, order_notional, asset_class="equity"
                            )
                        except Exception as exc:  # noqa: BLE001 - broker failures must not stop daemon
                            response = {
                                "status": "error",
                                "error_type": type(exc).__name__,
                                "message": str(exc),
                                "symbol": symbol,
                                "side": side,
                                "notional": order_notional,
                                "asset_class": "equity",
                            }
            event_notional = float(response.get("notional", notional))
            event = {
                "model_name": "__orphan_position_guard__",
                "symbol": symbol,
                "side": event_side,
                "notional": event_notional,
                "asset_class": "equity",
                "dry_run": self.config.dry_run,
                "response": response,
            }
            self.store.save_trade_event(event)
            events.append(event)
