from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from .alpaca_client import AlpacaGateway
from .backtest import BacktestConfig, run_backtest
from .config import DEFAULT_DB_PATH, AlpacaConfig
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
    symbols: str = typer.Option(..., help="Comma-separated symbols, e.g. AAPL,MSFT or BTC/USD,ETH/USD"),
    start: str = typer.Option(..., help="Start date YYYY-MM-DD"),
    end: str = typer.Option(..., help="End date YYYY-MM-DD"),
    data_csv: Optional[Path] = typer.Option(None, help="Local OHLCV CSV; omit to use Alpaca"),
    timeframe: str = typer.Option("1Day"),
    initial_cash: float = typer.Option(100_000.0),
    asset_class: str = typer.Option("equity", help="Asset class for Alpaca data/metadata: equity or crypto"),
    fee_maker_bps: float = typer.Option(0.0, help="Maker fee assumption in basis points"),
    fee_taker_bps: float = typer.Option(0.0, help="Taker fee assumption in basis points"),
    fill_mix: str = typer.Option("unknown", help="Fee fill assumption: maker, taker, mixed, or unknown"),
    db: Optional[Path] = typer.Option(None, help="SQLite database path"),
):
    symbol_list = _symbols(symbols)
    if data_csv:
        prices = load_price_csv(data_csv)
    else:
        prices = AlpacaGateway().get_bars(
            symbol_list, start=start, end=end, timeframe=timeframe, asset_class=asset_class
        )
    config = BacktestConfig(
        model_path=str(model_path),
        symbols=symbol_list,
        start=start,
        end=end,
        timeframe=timeframe,
        initial_cash=initial_cash,
        asset_class=asset_class,
        fee_maker_bps=fee_maker_bps,
        fee_taker_bps=fee_taker_bps,
        fill_mix=fill_mix,
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
    asset_class: str = typer.Option("equity", help="Asset class for this model: equity or crypto"),
    db: Optional[Path] = None,
):
    _store(db).upsert_model(
        name, str(model_path.expanduser().resolve()), allocation, _symbols(symbols), asset_class=asset_class
    )
    _print_json({"status": "ok", "name": name, "asset_class": asset_class})


@models_app.command("update")
def model_update(
    name: str,
    model_path: Path,
    allocation: float = typer.Option(..., min=0.0, max=1.0),
    symbols: str = typer.Option(...),
    asset_class: str = typer.Option("equity", help="Asset class for this model: equity or crypto"),
    db: Optional[Path] = None,
):
    _store(db).upsert_model(
        name, str(model_path.expanduser().resolve()), allocation, _symbols(symbols), asset_class=asset_class
    )
    _print_json({"status": "ok", "name": name, "asset_class": asset_class})


@models_app.command("remove")
def model_remove(name: str, db: Optional[Path] = None):
    _store(db).remove_model(name)
    _print_json({"status": "ok", "name": name})


@models_app.command("list")
def model_list(
    asset_class: Optional[str] = typer.Option(None, help="Filter by asset class: equity or crypto"),
    db: Optional[Path] = None,
):
    _print_json(_store(db).list_models(asset_class=asset_class))


@daemon_app.command("run")
def daemon_run(
    interval_seconds: int = typer.Option(300),
    submit_orders: bool = typer.Option(
        False,
        "--submit-orders",
        help="Submit orders to the configured Alpaca account. Default is simulation/no-submit.",
    ),
    allow_live_brokerage: bool = typer.Option(
        False,
        "--allow-live-brokerage",
        help="Permit order submission when ALPACA_PAPER=false. Required for live brokerage.",
    ),
    dry_run: Optional[bool] = typer.Option(
        None,
        "--dry-run/--no-dry-run",
        hidden=True,
        help="Deprecated: use default simulation mode or --submit-orders.",
    ),
    live: bool = typer.Option(False, "--live", hidden=True, help="Deprecated live-order interlock."),
    once: bool = typer.Option(False, help="Run one tick and exit"),
    db: Optional[Path] = None,
):
    effective_dry_run = not submit_orders
    store = _store(db)
    active_asset_classes = sorted(
        {model.get("asset_class", "equity") for model in store.list_models(active_only=True)}
    )
    asset_class_summary = ",".join(active_asset_classes) if active_asset_classes else "none"

    if effective_dry_run:
        typer.echo(
            f"SIMULATION ONLY: no Alpaca orders will be submitted. active_asset_classes={asset_class_summary}"
        )
    else:
        alpaca_config = AlpacaConfig.from_env()
        if not alpaca_config.paper and not allow_live_brokerage:
            typer.echo(
                "Refusing to submit live brokerage orders: ALPACA_PAPER=false requires "
                "--allow-live-brokerage.",
                err=True,
            )
            raise typer.Exit(code=1)
        account_mode = "paper" if alpaca_config.paper else "live brokerage"
        typer.echo(
            f"Submitting orders to Alpaca {account_mode} account. active_asset_classes={asset_class_summary}"
        )

    daemon = TradingDaemon(
        store=store,
        alpaca=AlpacaGateway(),
        config=DaemonConfig(interval_seconds=interval_seconds, dry_run=effective_dry_run, once=once),
    )
    daemon.run()
