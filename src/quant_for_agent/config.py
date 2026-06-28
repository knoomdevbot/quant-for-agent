from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_HOME = Path(os.environ.get("QFA_HOME", Path.home() / ".qfa"))
DEFAULT_DB_PATH = Path(os.environ.get("QFA_DB", DEFAULT_HOME / "qfa.sqlite3"))


@dataclass(frozen=True)
class AlpacaConfig:
    api_key: str
    secret_key: str
    paper: bool = True
    data_feed: str | None = None

    @classmethod
    def from_env(cls) -> "AlpacaConfig":
        api_key = os.environ.get("ALPACA_API_KEY")
        secret_key = os.environ.get("ALPACA_SECRET_KEY")
        if not api_key or not secret_key:
            raise RuntimeError("ALPACA_API_KEY and ALPACA_SECRET_KEY are required")
        paper = os.environ.get("ALPACA_PAPER", "true").lower() not in {"0", "false", "no"}
        data_feed = os.environ.get("ALPACA_DATA_FEED")
        return cls(
            api_key=api_key,
            secret_key=secret_key,
            paper=paper,
            data_feed=data_feed.lower() if data_feed else None,
        )
