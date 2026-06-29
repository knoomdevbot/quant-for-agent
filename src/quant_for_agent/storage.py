from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .config import DEFAULT_DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS backtest_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  model_path TEXT NOT NULL,
  symbols TEXT NOT NULL,
  asset_class TEXT NOT NULL DEFAULT 'equity',
  asset_bucket TEXT NOT NULL DEFAULT 'equity',
  crypto_label INTEGER NOT NULL DEFAULT 0,
  fee_model_json TEXT NOT NULL DEFAULT '{}',
  start TEXT NOT NULL,
  end TEXT NOT NULL,
  timeframe TEXT NOT NULL,
  initial_cash REAL NOT NULL,
  metrics_json TEXT NOT NULL,
  equity_curve_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS alpha_models (
  name TEXT PRIMARY KEY,
  model_path TEXT NOT NULL,
  allocation REAL NOT NULL CHECK (allocation >= 0 AND allocation <= 1),
  symbols TEXT NOT NULL,
  asset_class TEXT NOT NULL DEFAULT 'equity',
  active INTEGER NOT NULL DEFAULT 1,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trade_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  model_name TEXT,
  symbol TEXT NOT NULL,
  side TEXT NOT NULL,
  notional REAL NOT NULL,
  dry_run INTEGER NOT NULL,
  response_json TEXT NOT NULL
);
"""

SUPPORTED_ASSET_CLASSES = {"equity", "crypto"}


def _normalize_asset_class(asset_class: str) -> str:
    normalized = asset_class.strip().lower()
    if normalized not in SUPPORTED_ASSET_CLASSES:
        supported = ", ".join(sorted(SUPPORTED_ASSET_CLASSES))
        raise ValueError(f"Unsupported asset_class {asset_class!r}; expected one of: {supported}")
    return normalized


class Store:
    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self._migrate_schema()
        self.conn.commit()

    def _migrate_schema(self) -> None:
        self._add_column_if_missing("backtest_runs", "asset_class", "TEXT NOT NULL DEFAULT 'equity'")
        self._add_column_if_missing("backtest_runs", "asset_bucket", "TEXT NOT NULL DEFAULT 'equity'")
        self._add_column_if_missing("backtest_runs", "crypto_label", "INTEGER NOT NULL DEFAULT 0")
        self._add_column_if_missing("backtest_runs", "fee_model_json", "TEXT NOT NULL DEFAULT '{}'")
        self._add_column_if_missing("alpha_models", "asset_class", "TEXT NOT NULL DEFAULT 'equity'")

    def _add_column_if_missing(self, table: str, column: str, definition: str) -> None:
        columns = {row["name"] for row in self.conn.execute(f"PRAGMA table_info({table})")}
        if column not in columns:
            self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    def close(self) -> None:
        self.conn.close()

    def save_backtest(self, run: dict[str, Any]) -> int:
        asset_class = _normalize_asset_class(run.get("asset_class", "equity"))
        asset_bucket = run.get("asset_bucket") or ("crypto" if asset_class == "crypto" else "equity")
        crypto_label = bool(run.get("crypto_label", asset_class == "crypto"))
        cur = self.conn.execute(
            """
            INSERT INTO backtest_runs
            (model_path, symbols, asset_class, asset_bucket, crypto_label, fee_model_json, start, end, timeframe, initial_cash, metrics_json, equity_curve_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run["model_path"],
                json.dumps(run["symbols"]),
                asset_class,
                asset_bucket,
                1 if crypto_label else 0,
                json.dumps(run.get("fee_model", {}), sort_keys=True),
                run["start"],
                run["end"],
                run["timeframe"],
                run["initial_cash"],
                json.dumps(run["metrics"], sort_keys=True),
                json.dumps(run["equity_curve"]),
            ),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def list_backtests(self, limit: int = 20) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM backtest_runs ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [self._decode_backtest(row) for row in rows]

    def get_backtest(self, run_id: int) -> dict[str, Any] | None:
        row = self.conn.execute("SELECT * FROM backtest_runs WHERE id = ?", (run_id,)).fetchone()
        return self._decode_backtest(row) if row else None

    def upsert_model(
        self,
        name: str,
        model_path: str,
        allocation: float,
        symbols: list[str],
        asset_class: str = "equity",
    ) -> None:
        normalized_asset_class = _normalize_asset_class(asset_class)
        self.conn.execute(
            """
            INSERT INTO alpha_models (name, model_path, allocation, symbols, asset_class, active, updated_at)
            VALUES (?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(name) DO UPDATE SET
              model_path=excluded.model_path,
              allocation=excluded.allocation,
              symbols=excluded.symbols,
              asset_class=excluded.asset_class,
              active=1,
              updated_at=CURRENT_TIMESTAMP
            """,
            (name, model_path, allocation, json.dumps(symbols), normalized_asset_class),
        )
        self.conn.commit()

    def remove_model(self, name: str) -> None:
        self.conn.execute("DELETE FROM alpha_models WHERE name = ?", (name,))
        self.conn.commit()

    def list_models(self, active_only: bool = False) -> list[dict[str, Any]]:
        sql = "SELECT * FROM alpha_models"
        if active_only:
            sql += " WHERE active = 1"
        sql += " ORDER BY name"
        return [self._decode_model(row) for row in self.conn.execute(sql).fetchall()]

    def set_model_active(self, name: str, active: bool) -> None:
        self.conn.execute(
            "UPDATE alpha_models SET active = ?, updated_at = CURRENT_TIMESTAMP WHERE name = ?",
            (1 if active else 0, name),
        )
        self.conn.commit()

    def save_trade_event(self, event: dict[str, Any]) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO trade_events (model_name, symbol, side, notional, dry_run, response_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                event.get("model_name"),
                event["symbol"],
                event["side"],
                event["notional"],
                1 if event.get("dry_run", True) else 0,
                json.dumps(event.get("response", {}), sort_keys=True),
            ),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    @staticmethod
    def _decode_backtest(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["symbols"] = json.loads(data["symbols"])
        data["crypto_label"] = bool(data.get("crypto_label", 0))
        data["fee_model"] = json.loads(data.pop("fee_model_json", "{}") or "{}")
        data["metrics"] = json.loads(data.pop("metrics_json"))
        data["equity_curve"] = json.loads(data.pop("equity_curve_json"))
        return data

    @staticmethod
    def _decode_model(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["symbols"] = json.loads(data["symbols"])
        data["asset_class"] = data.get("asset_class") or "equity"
        data["active"] = bool(data["active"])
        return data
