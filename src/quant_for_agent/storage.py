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
  point_in_time_universe INTEGER NOT NULL DEFAULT 0,
  universe_spec_json TEXT NOT NULL DEFAULT '{}',
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
  asset_bucket TEXT NOT NULL DEFAULT 'equity',
  active INTEGER NOT NULL DEFAULT 1,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trade_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  model_name TEXT,
  symbol TEXT NOT NULL,
  asset_class TEXT NOT NULL DEFAULT 'equity',
  side TEXT NOT NULL,
  notional REAL NOT NULL,
  dry_run INTEGER NOT NULL,
  response_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS daemon_status (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  pid INTEGER,
  mode TEXT NOT NULL,
  paper INTEGER,
  data_feed TEXT,
  status TEXT NOT NULL,
  last_tick_started_at TEXT,
  last_tick_finished_at TEXT,
  next_tick_at TEXT,
  last_error_type TEXT,
  last_error_message TEXT
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
        self._add_column_if_missing(
            "backtest_runs", "point_in_time_universe", "INTEGER NOT NULL DEFAULT 0"
        )
        self._add_column_if_missing("backtest_runs", "universe_spec_json", "TEXT NOT NULL DEFAULT '{}'")
        self._add_column_if_missing("alpha_models", "asset_class", "TEXT NOT NULL DEFAULT 'equity'")
        self._add_column_if_missing("alpha_models", "asset_bucket", "TEXT NOT NULL DEFAULT 'equity'")
        self.conn.execute(
            "UPDATE alpha_models SET asset_bucket = 'crypto' "
            "WHERE asset_class = 'crypto' AND asset_bucket = 'equity'"
        )
        self._add_column_if_missing("trade_events", "asset_class", "TEXT NOT NULL DEFAULT 'equity'")

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
            (model_path, symbols, asset_class, asset_bucket, crypto_label, fee_model_json, point_in_time_universe, universe_spec_json, start, end, timeframe, initial_cash, metrics_json, equity_curve_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run["model_path"],
                json.dumps(run["symbols"]),
                asset_class,
                asset_bucket,
                1 if crypto_label else 0,
                json.dumps(run.get("fee_model", {}), sort_keys=True),
                1 if run.get("point_in_time_universe", False) else 0,
                json.dumps(run.get("universe_spec", {}), sort_keys=True),
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
        asset_bucket = "crypto" if normalized_asset_class == "crypto" else "equity"
        self.conn.execute(
            """
            INSERT INTO alpha_models (name, model_path, allocation, symbols, asset_class, asset_bucket, active, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(name) DO UPDATE SET
              model_path=excluded.model_path,
              allocation=excluded.allocation,
              symbols=excluded.symbols,
              asset_class=excluded.asset_class,
              asset_bucket=excluded.asset_bucket,
              active=1,
              updated_at=CURRENT_TIMESTAMP
            """,
            (name, model_path, allocation, json.dumps(symbols), normalized_asset_class, asset_bucket),
        )
        self.conn.commit()

    def remove_model(self, name: str) -> None:
        self.conn.execute("DELETE FROM alpha_models WHERE name = ?", (name,))
        self.conn.commit()

    def list_models(
        self, active_only: bool = False, asset_class: str | None = None
    ) -> list[dict[str, Any]]:
        sql = "SELECT * FROM alpha_models"
        filters = []
        params: list[Any] = []
        if active_only:
            filters.append("active = 1")
        if asset_class is not None:
            filters.append("asset_class = ?")
            params.append(_normalize_asset_class(asset_class))
        if filters:
            sql += " WHERE " + " AND ".join(filters)
        sql += " ORDER BY name"
        return [self._decode_model(row) for row in self.conn.execute(sql, params).fetchall()]

    def set_model_active(self, name: str, active: bool) -> None:
        self.conn.execute(
            "UPDATE alpha_models SET active = ?, updated_at = CURRENT_TIMESTAMP WHERE name = ?",
            (1 if active else 0, name),
        )
        self.conn.commit()

    def save_trade_event(self, event: dict[str, Any]) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO trade_events (model_name, symbol, asset_class, side, notional, dry_run, response_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.get("model_name"),
                event["symbol"],
                _normalize_asset_class(event.get("asset_class", "equity"))
                if event.get("asset_class", "equity") != "mixed"
                else "mixed",
                event["side"],
                event["notional"],
                1 if event.get("dry_run", True) else 0,
                json.dumps(event.get("response", {}), sort_keys=True),
            ),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def save_daemon_status(self, status: dict[str, Any]) -> None:
        self.conn.execute(
            """
            INSERT INTO daemon_status (
              id, pid, mode, paper, data_feed, status, last_tick_started_at,
              last_tick_finished_at, next_tick_at, last_error_type, last_error_message, updated_at
            ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
              pid=excluded.pid,
              mode=excluded.mode,
              paper=excluded.paper,
              data_feed=excluded.data_feed,
              status=excluded.status,
              last_tick_started_at=excluded.last_tick_started_at,
              last_tick_finished_at=excluded.last_tick_finished_at,
              next_tick_at=excluded.next_tick_at,
              last_error_type=excluded.last_error_type,
              last_error_message=excluded.last_error_message,
              updated_at=CURRENT_TIMESTAMP
            """,
            (
                status.get("pid"),
                status["mode"],
                None if status.get("paper") is None else (1 if status.get("paper") else 0),
                status.get("data_feed"),
                status["status"],
                status.get("last_tick_started_at"),
                status.get("last_tick_finished_at"),
                status.get("next_tick_at"),
                status.get("last_error_type"),
                status.get("last_error_message"),
            ),
        )
        self.conn.commit()

    def get_daemon_status(self) -> dict[str, Any] | None:
        row = self.conn.execute("SELECT * FROM daemon_status WHERE id = 1").fetchone()
        if row is None:
            return None
        data = dict(row)
        data["paper"] = None if data.get("paper") is None else bool(data["paper"])
        return data

    def recover_daemon_status(self, reason: str = "manual_recovery") -> None:
        self.save_daemon_status(
            {
                "pid": None,
                "mode": "simulation",
                "paper": None,
                "data_feed": None,
                "status": "recovered",
                "last_tick_started_at": None,
                "last_tick_finished_at": None,
                "next_tick_at": None,
                "last_error_type": None,
                "last_error_message": reason,
            }
        )

    @staticmethod
    def _decode_backtest(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["symbols"] = json.loads(data["symbols"])
        data["crypto_label"] = bool(data.get("crypto_label", 0))
        data["point_in_time_universe"] = bool(data.get("point_in_time_universe", 0))
        data["fee_model"] = json.loads(data.pop("fee_model_json", "{}") or "{}")
        data["universe_spec"] = json.loads(data.pop("universe_spec_json", "{}") or "{}")
        data["metrics"] = json.loads(data.pop("metrics_json"))
        data["equity_curve"] = json.loads(data.pop("equity_curve_json"))
        return data

    @staticmethod
    def _decode_model(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["symbols"] = json.loads(data["symbols"])
        data["asset_class"] = data.get("asset_class") or "equity"
        data["asset_bucket"] = data.get("asset_bucket") or (
            "crypto" if data["asset_class"] == "crypto" else "equity"
        )
        data["active"] = bool(data["active"])
        return data
