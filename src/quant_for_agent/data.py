from __future__ import annotations

from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = {"timestamp", "symbol", "open", "high", "low", "close", "volume"}


def load_price_csv(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(Path(path).expanduser())
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Price CSV missing required columns: {sorted(missing)}")
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df.sort_values(["timestamp", "symbol"]).reset_index(drop=True)
