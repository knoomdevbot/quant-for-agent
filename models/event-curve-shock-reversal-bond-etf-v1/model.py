"""AR-070 scheduled macro-event curve-shock reversal bond ETF alpha.

QFA contract: expose generate_signals(context) -> dict[str, float].

Research-only, long-only event model for scheduled FOMC/CPI/NFP/PPI windows.
The calendar is explicit and public (FOMC statement dates plus BLS CPI/PPI and
jobs release dates, 2019-2025 subset used in the evaluation); no continuous
AR-061 carry state is used.  The model is flat outside the first five trading
sessions after a scheduled event and sizes duration/inflation/credit ETF sleeves
from event-day ETF shocks only.
"""
from __future__ import annotations

# Some scheduled macro dates legitimately contain multiple event labels on the
# same day in this compact calendar; the final label is sufficient for the
# model's binary event-gate behavior.
# ruff: noqa: F601

import math
from typing import Dict

import pandas as pd

UNIVERSE = ("SHY", "IEF", "TLT", "TIP", "LQD", "HYG", "GLD", "SPY")
MIN_HISTORY = 130
ZSCORE_WINDOW = 126
EVENT_HOLD_DAYS = 5
MAX_GROSS = 1.0
MAX_SINGLE = 0.42
MAX_CREDIT = 0.18

# Explicit public macro-event calendar. Dates are US release/statement dates.
# Categories are intentionally not consumed by qfa, but retained for auditability.
EVENTS = {
    # 2019 FOMC, CPI, payroll/NFP, selected PPI
    "2019-01-04":"NFP", "2019-01-11":"CPI", "2019-01-30":"FOMC", "2019-02-01":"NFP", "2019-02-13":"CPI", "2019-03-08":"NFP", "2019-03-12":"CPI", "2019-03-20":"FOMC", "2019-04-05":"NFP", "2019-04-10":"CPI", "2019-05-01":"FOMC", "2019-05-03":"NFP", "2019-05-10":"CPI", "2019-06-07":"NFP", "2019-06-12":"CPI", "2019-06-19":"FOMC", "2019-07-05":"NFP", "2019-07-11":"CPI", "2019-07-31":"FOMC", "2019-08-02":"NFP", "2019-08-13":"CPI", "2019-09-06":"NFP", "2019-09-12":"CPI", "2019-09-18":"FOMC", "2019-10-04":"NFP", "2019-10-10":"CPI", "2019-10-30":"FOMC", "2019-11-01":"NFP", "2019-11-13":"CPI", "2019-12-06":"NFP", "2019-12-11":"FOMC", "2019-12-11":"CPI",
    # 2020
    "2020-01-10":"NFP", "2020-01-14":"CPI", "2020-01-29":"FOMC", "2020-02-07":"NFP", "2020-02-13":"CPI", "2020-03-06":"NFP", "2020-03-11":"CPI", "2020-03-15":"FOMC", "2020-04-03":"NFP", "2020-04-10":"CPI", "2020-04-29":"FOMC", "2020-05-08":"NFP", "2020-05-12":"CPI", "2020-06-05":"NFP", "2020-06-10":"CPI", "2020-06-10":"FOMC", "2020-07-02":"NFP", "2020-07-14":"CPI", "2020-07-29":"FOMC", "2020-08-07":"NFP", "2020-08-12":"CPI", "2020-09-04":"NFP", "2020-09-11":"CPI", "2020-09-16":"FOMC", "2020-10-02":"NFP", "2020-10-13":"CPI", "2020-11-06":"NFP", "2020-11-12":"CPI", "2020-12-04":"NFP", "2020-12-10":"CPI", "2020-12-16":"FOMC",
    # 2021
    "2021-01-08":"NFP", "2021-01-13":"CPI", "2021-01-27":"FOMC", "2021-02-05":"NFP", "2021-02-10":"CPI", "2021-03-05":"NFP", "2021-03-10":"CPI", "2021-03-17":"FOMC", "2021-04-02":"NFP", "2021-04-13":"CPI", "2021-04-28":"FOMC", "2021-05-07":"NFP", "2021-05-12":"CPI", "2021-06-04":"NFP", "2021-06-10":"CPI", "2021-06-16":"FOMC", "2021-07-02":"NFP", "2021-07-13":"CPI", "2021-07-28":"FOMC", "2021-08-06":"NFP", "2021-08-11":"CPI", "2021-09-03":"NFP", "2021-09-14":"CPI", "2021-09-22":"FOMC", "2021-10-08":"NFP", "2021-10-13":"CPI", "2021-11-03":"FOMC", "2021-11-05":"NFP", "2021-11-10":"CPI", "2021-12-03":"NFP", "2021-12-10":"CPI", "2021-12-15":"FOMC",
    # 2022
    "2022-01-07":"NFP", "2022-01-12":"CPI", "2022-01-26":"FOMC", "2022-02-04":"NFP", "2022-02-10":"CPI", "2022-03-04":"NFP", "2022-03-10":"CPI", "2022-03-16":"FOMC", "2022-04-01":"NFP", "2022-04-12":"CPI", "2022-05-04":"FOMC", "2022-05-06":"NFP", "2022-05-11":"CPI", "2022-06-03":"NFP", "2022-06-10":"CPI", "2022-06-15":"FOMC", "2022-07-08":"NFP", "2022-07-13":"CPI", "2022-07-27":"FOMC", "2022-08-05":"NFP", "2022-08-10":"CPI", "2022-09-02":"NFP", "2022-09-13":"CPI", "2022-09-21":"FOMC", "2022-10-07":"NFP", "2022-10-13":"CPI", "2022-11-02":"FOMC", "2022-11-04":"NFP", "2022-11-10":"CPI", "2022-12-02":"NFP", "2022-12-13":"CPI", "2022-12-14":"FOMC",
    # 2023
    "2023-01-06":"NFP", "2023-01-12":"CPI", "2023-02-01":"FOMC", "2023-02-03":"NFP", "2023-02-14":"CPI", "2023-03-10":"NFP", "2023-03-14":"CPI", "2023-03-22":"FOMC", "2023-04-07":"NFP", "2023-04-12":"CPI", "2023-05-03":"FOMC", "2023-05-05":"NFP", "2023-05-10":"CPI", "2023-06-02":"NFP", "2023-06-13":"CPI", "2023-06-14":"FOMC", "2023-07-07":"NFP", "2023-07-12":"CPI", "2023-07-26":"FOMC", "2023-08-04":"NFP", "2023-08-10":"CPI", "2023-09-01":"NFP", "2023-09-13":"CPI", "2023-09-20":"FOMC", "2023-10-06":"NFP", "2023-10-12":"CPI", "2023-11-01":"FOMC", "2023-11-03":"NFP", "2023-11-14":"CPI", "2023-12-08":"NFP", "2023-12-12":"CPI", "2023-12-13":"FOMC",
    # 2024
    "2024-01-05":"NFP", "2024-01-11":"CPI", "2024-01-31":"FOMC", "2024-02-02":"NFP", "2024-02-13":"CPI", "2024-03-08":"NFP", "2024-03-12":"CPI", "2024-03-20":"FOMC", "2024-04-05":"NFP", "2024-04-10":"CPI", "2024-05-01":"FOMC", "2024-05-03":"NFP", "2024-05-15":"CPI", "2024-06-07":"NFP", "2024-06-12":"CPI", "2024-06-12":"FOMC", "2024-07-05":"NFP", "2024-07-11":"CPI", "2024-07-31":"FOMC", "2024-08-02":"NFP", "2024-08-14":"CPI", "2024-09-06":"NFP", "2024-09-11":"CPI", "2024-09-18":"FOMC", "2024-10-04":"NFP", "2024-10-10":"CPI", "2024-11-01":"NFP", "2024-11-07":"FOMC", "2024-11-13":"CPI", "2024-12-06":"NFP", "2024-12-11":"CPI", "2024-12-18":"FOMC",
    # 2025 through evaluation end plus known 2025 FOMC/CPI/NFP dates
    "2025-01-10":"NFP", "2025-01-15":"CPI", "2025-01-29":"FOMC", "2025-02-07":"NFP", "2025-02-12":"CPI", "2025-03-07":"NFP", "2025-03-12":"CPI", "2025-03-19":"FOMC", "2025-04-04":"NFP", "2025-04-10":"CPI", "2025-05-02":"NFP", "2025-05-07":"FOMC", "2025-05-13":"CPI", "2025-06-06":"NFP", "2025-06-11":"CPI", "2025-06-18":"FOMC", "2025-07-03":"NFP", "2025-07-15":"CPI", "2025-07-30":"FOMC", "2025-08-01":"NFP", "2025-08-12":"CPI", "2025-09-05":"NFP", "2025-09-11":"CPI", "2025-09-17":"FOMC", "2025-10-03":"NFP", "2025-10-15":"CPI", "2025-10-29":"FOMC", "2025-11-07":"NFP", "2025-11-13":"CPI", "2025-12-05":"NFP", "2025-12-10":"FOMC", "2025-12-10":"CPI",
}
EVENT_DATES = frozenset(EVENTS.keys())


def _safe(x: float, default: float = 0.0) -> float:
    try:
        y = float(x)
    except Exception:
        return default
    return y if math.isfinite(y) else default


def _event_idx(index: pd.DatetimeIndex, as_of: pd.Timestamp) -> tuple[int | None, int | None]:
    dates = [d.strftime("%Y-%m-%d") for d in index]
    last_pos = None
    for i, d in enumerate(dates):
        if d in EVENT_DATES and index[i] <= as_of:
            last_pos = i
    if last_pos is None:
        return None, None
    age = len(index) - 1 - last_pos
    return (last_pos, age) if 0 <= age <= EVENT_HOLD_DAYS else (None, None)


def _zscore(ret: pd.Series, pos: int, window: int) -> float:
    if pos < window or pos >= len(ret):
        return 0.0
    hist = ret.iloc[pos - window:pos].dropna()
    sd = _safe(hist.std(ddof=1))
    if len(hist) < 40 or sd <= 1e-8:
        return 0.0
    return max(-3.0, min(3.0, _safe((ret.iloc[pos] - hist.mean()) / sd)))


def _add(weights: Dict[str, float], symbol: str, amount: float) -> None:
    if symbol in weights:
        weights[symbol] = weights.get(symbol, 0.0) + max(0.0, amount)


def _cap_normalize(weights: Dict[str, float]) -> Dict[str, float]:
    # cap single-name and credit sleeve, then normalize to <= MAX_GROSS.
    for s in list(weights):
        weights[s] = min(max(0.0, _safe(weights[s])), MAX_SINGLE)
    credit = weights.get("LQD", 0.0) + weights.get("HYG", 0.0)
    if credit > MAX_CREDIT:
        scale = MAX_CREDIT / credit
        weights["LQD"] = weights.get("LQD", 0.0) * scale
        weights["HYG"] = weights.get("HYG", 0.0) * scale
    gross = sum(abs(v) for v in weights.values())
    if gross > MAX_GROSS:
        weights = {s: v * MAX_GROSS / gross for s, v in weights.items()}
    return weights


def generate_signals(context) -> dict[str, float]:
    symbols = list(context.symbols)
    flat = {s: 0.0 for s in symbols}
    if context.prices is None or context.prices.empty:
        return flat

    prices = context.prices.copy()
    prices["timestamp"] = pd.to_datetime(prices["timestamp"], utc=True)
    close = prices.pivot(index="timestamp", columns="symbol", values="close").sort_index().ffill()
    available = [s for s in UNIVERSE if s in symbols and s in close.columns]
    if len(close) < MIN_HISTORY or not {"SHY", "IEF", "TLT", "TIP"}.issubset(set(available)):
        return flat

    as_of = pd.Timestamp(context.as_of).tz_convert("UTC") if pd.Timestamp(context.as_of).tzinfo else pd.Timestamp(context.as_of, tz="UTC")
    close = close.loc[close.index <= as_of]
    event_pos, age = _event_idx(close.index, as_of)
    if event_pos is None or age is None:
        return flat

    returns = close.pct_change().fillna(0.0)
    z_tlt = _zscore(returns["TLT"], event_pos, ZSCORE_WINDOW)
    z_ief = _zscore(returns["IEF"], event_pos, ZSCORE_WINDOW)
    z_tip = _zscore(returns["TIP"], event_pos, ZSCORE_WINDOW)
    z_shy = _zscore(returns["SHY"], event_pos, ZSCORE_WINDOW)
    z_lqd = _zscore(returns["LQD"], event_pos, ZSCORE_WINDOW) if "LQD" in returns else 0.0
    z_hyg = _zscore(returns["HYG"], event_pos, ZSCORE_WINDOW) if "HYG" in returns else 0.0
    z_spy = _zscore(returns["SPY"], event_pos, ZSCORE_WINDOW) if "SPY" in returns else 0.0
    z_gld = _zscore(returns["GLD"], event_pos, ZSCORE_WINDOW) if "GLD" in returns else 0.0

    duration_shock = 0.55 * z_tlt + 0.35 * z_ief - 0.10 * z_shy
    inflation_shock = z_tip - 0.55 * z_ief + 0.20 * z_gld
    credit_shock = 0.55 * z_hyg + 0.45 * z_lqd - 0.25 * z_ief
    risk_shock = 0.60 * z_spy + 0.40 * z_hyg

    # Decay exposure after the announcement; age=0 is positioned for next day.
    decay = [1.00, 0.82, 0.62, 0.45, 0.32, 0.22][age]
    shock_mag = min(1.0, max(abs(duration_shock), abs(inflation_shock), abs(credit_shock)) / 1.75)
    budget = decay * (0.30 + 0.70 * shock_mag)
    if budget < 0.10:
        return flat

    weights = {s: 0.0 for s in symbols}

    # Duration reversal: sharp selloff in TLT/IEF often receives next-day demand;
    # sharp rally is treated defensively via SHY/TIP rather than shorting.
    if duration_shock <= -0.45:
        _add(weights, "TLT", budget * 0.40)
        _add(weights, "IEF", budget * 0.30)
        _add(weights, "TIP", budget * 0.15)
        _add(weights, "GLD", budget * 0.05)
    elif duration_shock >= 0.70:
        _add(weights, "SHY", budget * 0.45)
        _add(weights, "IEF", budget * 0.18)
        _add(weights, "TIP", budget * 0.12)
    else:
        _add(weights, "IEF", budget * 0.22)
        _add(weights, "SHY", budget * 0.18)

    # Inflation hedge response: TIP/GLD get incremental weight after positive
    # inflation-sensitive shock; otherwise prefer nominal duration.
    if inflation_shock > 0.50:
        _add(weights, "TIP", budget * 0.25)
        _add(weights, "GLD", budget * 0.12)
    elif inflation_shock < -0.50:
        _add(weights, "IEF", budget * 0.16)
        _add(weights, "TLT", budget * 0.10)

    # Credit continuation/reversal split. Positive credit/risk shock can continue
    # briefly; negative shock shifts away from HYG into Treasuries.
    if credit_shock > 0.65 and risk_shock > 0.0:
        _add(weights, "HYG", budget * 0.10)
        _add(weights, "LQD", budget * 0.08)
        _add(weights, "SPY", budget * 0.05)
    elif credit_shock < -0.65 or risk_shock < -0.70:
        _add(weights, "IEF", budget * 0.16)
        _add(weights, "TLT", budget * 0.12)
        _add(weights, "SHY", budget * 0.10)

    return _cap_normalize(weights)
