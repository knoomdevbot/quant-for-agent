"""AR-147 FRED/Chicago Fed NFCI shock ETF allocator.

Predeclared primary source: Chicago Fed National Financial Conditions Index (NFCI)
via FRED. Direction: a positive 4-week NFCI shock means tighter financial
conditions, so allocate to a defensive/risk-off ETF sleeve for 10 trading days;
a negative shock means easing/relief, so allocate to a relief/risk-on sleeve.

Timestamp discipline: embedded dates are conservative availability dates equal
to FRED observation_date + 7 calendar days. The qfa daily backtester trades at
the close on/after that date and earns the next daily bar. This model embeds only
thresholded shock z-scores from 2017 onward; it does not retain raw FRED values,
raw market data, daily returns, or weights.

Research-only; no daemon, no orders.
"""
from __future__ import annotations

import pandas as pd
from typing import Any

UNIVERSE = [
    "SPY", "QQQ", "IWM", "DIA", "XLK", "XLI", "XLF", "XLV", "XLP", "XLU",
    "XLE", "XLB", "TLT", "IEF", "TIP", "LQD", "HYG", "SHY", "GLD", "DBC",
    "UUP", "FXE", "FXY", "VNQ", "USMV", "QUAL", "MTUM",
]
HOLD_TRADING_DAYS = 10
THRESHOLD_Z = 0.75
# (conservative_release_available_date, four-week NFCI shock z-score)
NFCI_SHOCKS = [('2017-01-06', -0.8497),
 ('2017-01-13', -0.7568),
 ('2017-05-05', -0.8189),
 ('2017-05-12', -1.0035),
 ('2017-05-19', -1.1002),
 ('2017-05-26', -1.1112),
 ('2017-06-02', -1.0675),
 ('2017-06-09', -0.9977),
 ('2017-06-16', -0.8483),
 ('2018-02-02', 1.0286),
 ('2018-02-09', 1.8023),
 ('2018-02-16', 2.5891),
 ('2018-02-23', 2.9892),
 ('2018-03-02', 3.0715),
 ('2018-03-09', 2.9564),
 ('2018-03-16', 2.6521),
 ('2018-03-23', 2.3863),
 ('2018-03-30', 2.0235),
 ('2018-04-06', 1.52),
 ('2018-04-13', 0.8315),
 ('2018-04-27', -0.8356),
 ('2018-05-04', -1.4038),
 ('2018-05-11', -1.6769),
 ('2018-05-18', -1.6367),
 ('2018-05-25', -1.2671),
 ('2018-06-22', 0.9767),
 ('2018-06-29', 1.1713),
 ('2018-07-06', 1.0961),
 ('2018-07-13', 0.8646),
 ('2018-08-10', -0.9254),
 ('2018-08-17', -1.0261),
 ('2018-08-24', -0.9729),
 ('2018-08-31', -0.8445),
 ('2018-10-12', 0.8787),
 ('2018-10-19', 1.2393),
 ('2018-10-26', 1.5465),
 ('2018-11-02', 1.8398),
 ('2018-11-09', 2.1163),
 ('2018-11-16', 2.2366),
 ('2018-11-23', 2.4488),
 ('2018-11-30', 2.6031),
 ('2018-12-07', 2.672),
 ('2018-12-14', 2.6944),
 ('2018-12-21', 2.4036),
 ('2018-12-28', 1.8616),
 ('2019-01-04', 1.0967),
 ('2019-01-18', -1.0079),
 ('2019-01-25', -1.9038),
 ('2019-02-01', -2.4806),
 ('2019-02-08', -2.7004),
 ('2019-02-15', -2.5898),
 ('2019-02-22', -2.3308),
 ('2019-03-01', -1.9903),
 ('2019-03-08', -1.5426),
 ('2019-03-15', -1.1147),
 ('2019-03-22', -0.7508),
 ('2019-05-31', 0.7828),
 ('2019-06-07', 0.9017),
 ('2019-06-14', 0.8311),
 ('2019-08-23', 0.8912),
 ('2019-08-30', 1.0974),
 ('2019-09-06', 1.1123),
 ('2019-09-13', 0.9933),
 ('2019-09-20', 0.8223),
 ('2019-11-01', -1.0722),
 ('2019-11-08', -1.2733),
 ('2019-11-15', -1.2842),
 ('2019-11-22', -1.0869),
 ('2020-01-17', -0.9382),
 ('2020-01-24', -1.5817),
 ('2020-01-31', -1.7422),
 ('2020-02-07', -1.3336),
 ('2020-02-21', 1.8703),
 ('2020-02-28', 4.0),
 ('2020-03-06', 4.0),
 ('2020-03-13', 4.0),
 ('2020-03-20', 4.0),
 ('2020-03-27', 4.0),
 ('2020-04-03', 4.0),
 ('2020-04-10', 3.2956),
 ('2020-04-17', 1.8183),
 ('2020-05-01', -1.0899),
 ('2020-05-08', -2.081),
 ('2020-05-15', -2.6231),
 ('2020-05-22', -2.7477),
 ('2020-05-29', -2.6319),
 ('2020-06-05', -2.3197),
 ('2020-06-12', -1.9104),
 ('2020-06-19', -1.4836),
 ('2020-06-26', -1.1002),
 ('2020-07-03', -0.7974),
 ('2022-03-11', 0.7944),
 ('2022-03-18', 0.8634),
 ('2022-03-25', 0.8679),
 ('2022-04-01', 0.803),
 ('2022-05-13', 0.8321),
 ('2022-05-20', 1.0222),
 ('2022-05-27', 1.2101),
 ('2022-06-03', 1.426),
 ('2022-06-10', 1.6422),
 ('2022-06-17', 1.8187),
 ('2022-06-24', 1.952),
 ('2022-07-01', 1.7898),
 ('2022-07-08', 1.4153),
 ('2022-07-15', 0.7685),
 ('2022-07-29', -0.9129),
 ('2022-08-05', -1.5196),
 ('2022-08-12', -1.7387),
 ('2022-08-19', -1.598),
 ('2022-08-26', -1.1029),
 ('2022-09-16', 1.1908),
 ('2022-09-23', 1.7449),
 ('2022-09-30', 2.0149),
 ('2022-10-07', 1.8937),
 ('2022-10-14', 1.4548),
 ('2022-10-21', 0.8134),
 ('2022-11-11', -1.3136),
 ('2022-11-18', -1.6599),
 ('2022-11-25', -1.6987),
 ('2022-12-02', -1.5479),
 ('2022-12-09', -1.2692),
 ('2022-12-16', -0.9903),
 ('2022-12-23', -0.8646),
 ('2022-12-30', -0.9145),
 ('2023-01-06', -1.2048),
 ('2023-01-13', -1.5912),
 ('2023-01-20', -1.9508),
 ('2023-01-27', -2.1335),
 ('2023-02-03', -2.0553),
 ('2023-02-10', -1.7016),
 ('2023-02-17', -1.1038),
 ('2023-03-10', 1.2729),
 ('2023-03-17', 1.8013),
 ('2023-03-24', 2.0602),
 ('2023-03-31', 1.8862),
 ('2023-04-07', 1.3272),
 ('2023-04-28', -0.8328),
 ('2023-05-05', -1.1233),
 ('2023-05-12', -1.2321),
 ('2023-05-19', -1.1456),
 ('2023-05-26', -0.9836),
 ('2023-06-02', -0.8052),
 ('2023-07-21', -0.9202),
 ('2023-07-28', -1.1122),
 ('2023-08-04', -1.26),
 ('2023-08-11', -1.4198),
 ('2023-08-18', -1.4281),
 ('2023-08-25', -1.3648),
 ('2023-09-01', -1.2163),
 ('2023-09-08', -0.9849),
 ('2023-12-01', -0.8304),
 ('2023-12-08', -0.9221),
 ('2023-12-15', -0.9051),
 ('2023-12-22', -0.8545),
 ('2023-12-29', -0.8085),
 ('2024-01-12', -0.7645),
 ('2024-07-05', 0.7999),
 ('2024-07-12', 0.7833),
 ('2024-07-19', 0.7547),
 ('2024-09-13', -0.8063),
 ('2024-09-20', -0.8163),
 ('2024-09-27', -0.76),
 ('2025-03-07', 1.0736),
 ('2025-03-14', 1.632),
 ('2025-03-21', 2.1765),
 ('2025-03-28', 2.6162),
 ('2025-04-04', 2.8053),
 ('2025-04-11', 2.6919),
 ('2025-04-18', 2.3698),
 ('2025-04-25', 1.687),
 ('2025-05-02', 0.9054),
 ('2025-05-16', -1.0083),
 ('2025-05-23', -1.5564),
 ('2025-05-30', -1.783),
 ('2025-06-06', -1.6802),
 ('2025-06-13', -1.4262),
 ('2025-06-20', -1.0579),
 ('2025-06-27', -0.7933),
 ('2025-11-14', 0.7684),
 ('2026-01-02', -0.7899),
 ('2026-01-09', -1.0824),
 ('2026-01-16', -1.2952),
 ('2026-01-23', -1.2157),
 ('2026-01-30', -0.8515),
 ('2026-02-20', 1.0835),
 ('2026-02-27', 1.6623),
 ('2026-03-06', 2.1334),
 ('2026-03-13', 2.3935),
 ('2026-03-20', 2.4007),
 ('2026-03-27', 2.1274),
 ('2026-04-03', 1.662),
 ('2026-04-10', 0.9083),
 ('2026-05-01', -0.9959),
 ('2026-05-08', -1.1041),
 ('2026-05-15', -0.959)]


def _normalize(weights: dict[str, float], allowed: set[str]) -> dict[str, float]:
    clean = {s: float(v) for s, v in weights.items() if s in allowed and abs(float(v)) > 1e-12}
    gross = sum(abs(v) for v in clean.values())
    if gross <= 0:
        return {"SHY": 1.0} if "SHY" in allowed else {}
    return {s: v / gross for s, v in clean.items()}


def _stress_weights(allowed: set[str]) -> dict[str, float]:
    return _normalize({"SHY": 0.25, "IEF": 0.20, "TLT": 0.15, "GLD": 0.20, "XLU": 0.10, "XLP": 0.10}, allowed)


def _relief_weights(allowed: set[str]) -> dict[str, float]:
    return _normalize({"SPY": 0.25, "QQQ": 0.20, "IWM": 0.15, "HYG": 0.15, "XLF": 0.10, "XLK": 0.10, "DBC": 0.05}, allowed)


def _cash_like_weights(allowed: set[str]) -> dict[str, float]:
    return _normalize({"SHY": 1.0}, allowed)


def _active_state(as_of: pd.Timestamp, trading_index: pd.DatetimeIndex) -> str:
    as_of = pd.Timestamp(as_of)
    if as_of.tzinfo is None:
        as_of = as_of.tz_localize("UTC")
    else:
        as_of = as_of.tz_convert("UTC")
    active_state = "cash"
    active_until = None
    for date_str, z in NFCI_SHOCKS:
        release_ts = pd.Timestamp(date_str, tz="UTC")
        if release_ts > as_of:
            break
        pos = trading_index.searchsorted(release_ts)
        if pos >= len(trading_index):
            continue
        until = trading_index[min(len(trading_index) - 1, pos + HOLD_TRADING_DAYS)]
        if as_of <= until:
            active_state = "stress" if z >= THRESHOLD_Z else "relief"
            active_until = until
    return active_state if active_until is not None else "cash"


def generate_signals(context: Any) -> dict[str, float]:
    allowed = set(getattr(context, "symbols", UNIVERSE))
    prices = getattr(context, "prices", None)
    if prices is None or len(prices) == 0:
        return _cash_like_weights(allowed)
    ts = pd.to_datetime(prices["timestamp"], utc=True)
    trading_index = pd.DatetimeIndex(sorted(ts.dropna().unique()))
    if len(trading_index) == 0:
        return _cash_like_weights(allowed)
    state = _active_state(pd.Timestamp(getattr(context, "as_of", trading_index[-1])), trading_index)
    if state == "stress":
        return _stress_weights(allowed)
    if state == "relief":
        return _relief_weights(allowed)
    return _cash_like_weights(allowed)
