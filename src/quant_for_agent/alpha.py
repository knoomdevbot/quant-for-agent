from __future__ import annotations

import importlib.util
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

import pandas as pd


@dataclass(frozen=True)
class AlphaContext:
    symbols: list[str]
    prices: pd.DataFrame
    as_of: pd.Timestamp
    metadata: dict[str, Any] = field(default_factory=dict)


Signals = dict[str, float]
AlphaFunction = Callable[[AlphaContext], Signals]


def load_alpha_module(path: str | Path) -> ModuleType:
    model_path = Path(path).expanduser().resolve()
    if not model_path.exists():
        raise FileNotFoundError(f"Alpha model not found: {model_path}")
    module_name = f"qfa_alpha_{model_path.stem}_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, model_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load alpha model: {model_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_alpha_function(path: str | Path) -> AlphaFunction:
    module = load_alpha_module(path)
    fn = getattr(module, "generate_signals", None)
    if not callable(fn):
        raise AttributeError("Alpha model must define callable generate_signals(context)")
    return fn


def normalize_weights(signals: Signals, allowed_symbols: list[str]) -> Signals:
    cleaned = {symbol: float(signals.get(symbol, 0.0)) for symbol in allowed_symbols}
    gross = sum(abs(value) for value in cleaned.values())
    if gross == 0:
        return {symbol: 0.0 for symbol in allowed_symbols}
    return {symbol: value / gross for symbol, value in cleaned.items()}
