from __future__ import annotations

import json
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import DEFAULT_HEALTH_LOG_PATH


def format_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def utc_now() -> str:
    return format_utc(datetime.now(timezone.utc))


def resolve_health_log_path(path: str | Path | None = None) -> Path:
    return Path(path or DEFAULT_HEALTH_LOG_PATH).expanduser()


def append_health_log(path: str | Path | None, payload: dict[str, Any]) -> None:
    log_path = resolve_health_log_path(path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = {"logged_at": utc_now(), **payload}
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def read_health_log(path: str | Path | None = None, limit: int = 20) -> list[dict[str, Any]]:
    log_path = resolve_health_log_path(path)
    if not log_path.exists():
        return []
    entries: deque[dict[str, Any]] = deque(maxlen=max(int(limit), 0))
    with log_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                entries.append({"event": "unparseable_health_log_line", "raw": line[:500]})
    return list(entries)
