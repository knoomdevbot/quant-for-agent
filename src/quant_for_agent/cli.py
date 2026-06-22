from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from .alpaca_client import AlpacaGateway
from .backtest import BacktestConfig, run_backtest
from .config import DEFAULT_DB_PATH
from .daemon import DaemonConfig, TradingDaemon
from .data import load_price_csv
from .storage import Store

app = typer.Typer(help="quant-for-agent CLI")
backtest_app = typer.Typer(help="Run and query backtests")
models_app = typer.Typer(help="Manage alpha models in the trading portfolio")
daemon_app = typer.Typer(help="Run the Alpaca trading daemon")
app.add_typer(backtest_app, name="backtest")
app.add_typer(models_app, name="models")
app.add_typer(daemon_app, name="daemon")


def _symbols(value: str) -> list[str]:
    return [item.strip().upper() for item in value.split(",") if item.strip()]


def _store(db: Optional[Path]) -> Store:
    return Store(db or DEFAULT_DB_PATH)


def _print_json(payload) -> None:
    typer.echo(json.dumps(payload, indent=2, sort_keys=True))


@backtest_app.command("run")
def backtest_run(
    model_path: Path = typer.Argument(..., help="Python alpha model file"),
    symbols: str = typer.Option(..., help="Comma-separated symbols, e.g. AAPL,MSFT"),
    start: str = typer.Option(..., help="Start date YYYY-MM-DD"),
    end: str = typer.Option(..., help="End date YYYY-MM-DD"),
    data_csv: Optional[Path] = typer.Option(None, help="Local OHLCV CSV; omit to use Alpaca"),
    timeframe: str = typer.Option("1Day"),
    initial_cash: float = typer.Option(100_000.0),
    db: Optional[Path] = typer.Option(None, help="SQLite database path"),
):
    symbol_list = _symbols(symbols)
    if data_csv:
        prices = load_price_csv(data_csv)
    else:
        prices = AlpacaGateway().get_bars(symbol_list, start=start, end=end, timeframe=timeframe)
    config = BacktestConfig(
        model_path=str(model_path),
        symbols=symbol_list,
        start=start,
        end=end,
        timeframe=timeframe,
        initial_cash=initial_cash,
    )
    result = run_backtest(config, prices)
    store = _store(db)
    run_id = store.save_backtest(result)
    result["id"] = run_id
    _print_json(result)


@backtest_app.command("list")
def backtest_list(limit: int = typer.Option(20), db: Optional[Path] = None):
    _print_json(_store(db).list_backtests(limit=limit))


@backtest_app.command("show")
def backtest_show(run_id: int, db: Optional[Path] = None):
    result = _store(db).get_backtest(run_id)
    if result is None:
        raise typer.Exit(code=1)
    _print_json(result)


@models_app.command("add")
def model_add(
    model_path: Path,
    name: str = typer.Option(...),
    allocation: float = typer.Option(..., min=0.0, max=1.0),
    symbols: str = typer.Option(...),
    db: Optional[Path] = None,
):
    _store(db).upsert_model(name, str(model_path.expanduser().resolve()), allocation, _symbols(symbols))
    _print_json({"status": "ok", "name": name})


@models_app.command("update")
def model_update(
    name: str,
    model_path: Path,
    allocation: float = typer.Option(..., min=0.0, max=1.0),
    symbols: str = typer.Option(...),
    db: Optional[Path] = None,
):
    _store(db).upsert_model(name, str(model_path.expanduser().resolve()), allocation, _symbols(symbols))
    _print_json({"status": "ok", "name": name})


@models_app.command("remove")
def model_remove(name: str, db: Optional[Path] = None):
    _store(db).remove_model(name)
    _print_json({"status": "ok", "name": name})


@models_app.command("list")
def model_list(db: Optional[Path] = None):
    _print_json(_store(db).list_models())


@daemon_app.command("run")
def daemon_run(
    interval_seconds: int = typer.Option(300),
    dry_run: bool = typer.Option(True, help="Keep true unless intentionally placing orders"),
    live: bool = typer.Option(False, help="Required to place Alpaca orders"),
    once: bool = typer.Option(False, help="Run one tick and exit"),
    db: Optional[Path] = None,
):
    effective_dry_run = dry_run or not live
    daemon = TradingDaemon(
        store=_store(db),
        alpaca=AlpacaGateway(),
        config=DaemonConfig(interval_seconds=interval_seconds, dry_run=effective_dry_run, once=once),
    )
    daemon.run()
