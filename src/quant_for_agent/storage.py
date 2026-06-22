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


class Store:
    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def save_backtest(self, run: dict[str, Any]) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO backtest_runs
            (model_path, symbols, start, end, timeframe, initial_cash, metrics_json, equity_curve_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run["model_path"],
                json.dumps(run["symbols"]),
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

    def upsert_model(self, name: str, model_path: str, allocation: float, symbols: list[str]) -> None:
        self.conn.execute(
            """
            INSERT INTO alpha_models (name, model_path, allocation, symbols, active, updated_at)
            VALUES (?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(name) DO UPDATE SET
              model_path=excluded.model_path,
              allocation=excluded.allocation,
              symbols=excluded.symbols,
              active=1,
              updated_at=CURRENT_TIMESTAMP
            """,
            (name, model_path, allocation, json.dumps(symbols)),
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
        data["metrics"] = json.loads(data.pop("metrics_json"))
        data["equity_curve"] = json.loads(data.pop("equity_curve_json"))
        return data

    @staticmethod
    def _decode_model(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["symbols"] = json.loads(data["symbols"])
        data["active"] = bool(data["active"])
        return data
