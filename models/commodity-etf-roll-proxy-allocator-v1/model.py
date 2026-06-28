from __future__ import annotations

import math
from typing import Any

import pandas as pd

SYMBOLS = [
    "USO", "USL", "BNO", "UNG", "UNL",
    "GLD", "IAU", "SLV", "CPER", "DBB",
    "DBA", "CORN", "WEAT", "SOYB",
    "DBC", "PDBC", "COMT", "GSG",
]
FAMILIES = {
    "oil_gas": ["USO", "USL", "BNO", "UNG", "UNL"],
    "metals": ["GLD", "IAU", "SLV", "CPER", "DBB"],
    "agriculture": ["DBA", "CORN", "WEAT", "SOYB"],
    "broad": ["DBC", "PDBC", "COMT", "GSG"],
}
SYMBOL_TO_SLEEVE = {s: sleeve for sleeve, symbols in FAMILIES.items() for s in symbols}


def _extract_close_history(context: Any) -> pd.DataFrame:
    """Return close-price matrix indexed by timestamp/date, columns by symbol.

    Accepted context forms:
    - pandas DataFrame already shaped as date x symbol close matrix.
    - pandas DataFrame of bars with columns timestamp/date, symbol, close.
    - dict with key close, prices, history, or bars containing either form above.
    """
    obj = context
    if isinstance(context, dict):
        for key in ("close", "prices", "history", "bars"):
            if key in context:
                obj = context[key]
                break
    if not isinstance(obj, pd.DataFrame):
        return pd.DataFrame(columns=SYMBOLS)
    df = obj.copy()
    cols = {c.lower(): c for c in df.columns}
    if "symbol" in cols and "close" in cols:
        date_col = cols.get("timestamp") or cols.get("date") or cols.get("datetime")
        if date_col is None:
            if isinstance(df.index, pd.MultiIndex):
                df = df.reset_index()
                cols = {c.lower(): c for c in df.columns}
                date_col = cols.get("timestamp") or cols.get("date") or cols.get("datetime")
        if date_col is not None:
            df[date_col] = pd.to_datetime(df[date_col])
            pivoted = df.pivot_table(index=date_col, columns=cols["symbol"], values=cols["close"], aggfunc="last")
            return pd.DataFrame(pivoted).sort_index()
    return pd.DataFrame(df[[c for c in df.columns if c in SYMBOLS]]).sort_index()


def _cap_weights(weights: pd.Series, symbol_cap: float = 0.15, sleeve_cap: float = 0.35) -> pd.Series:
    w = weights.clip(lower=0).fillna(0.0)
    if w.sum() <= 0:
        return w
    w = w / w.sum()
    w = w.clip(upper=symbol_cap)
    if w.sum() > 0:
        w = w / w.sum()
    for _ in range(5):
        changed = False
        for sleeve in set(SYMBOL_TO_SLEEVE.values()):
            sleeve_symbols = [s for s in w.index if SYMBOL_TO_SLEEVE.get(s) == sleeve]
            sleeve_weight = w.loc[sleeve_symbols].sum() if sleeve_symbols else 0.0
            if sleeve_weight > sleeve_cap:
                excess = sleeve_weight - sleeve_cap
                w.loc[sleeve_symbols] *= sleeve_cap / sleeve_weight
                others = [s for s in w.index if s not in sleeve_symbols and w.loc[s] < symbol_cap]
                room = sum(symbol_cap - w.loc[s] for s in others)
                if room > 0:
                    for s in others:
                        w.loc[s] += excess * (symbol_cap - w.loc[s]) / room
                changed = True
        w = w.clip(upper=symbol_cap)
        if not changed:
            break
    if w.sum() > 1.0:
        w = w / w.sum()
    return w.fillna(0.0)


def generate_signals(context: Any) -> dict[str, float]:
    """Generate long-only commodity ETF allocator weights.

    The signal is timestamp-safe for daily bars: all features use only the latest
    available close history through the context date, and an evaluator should
    apply returned weights to subsequent returns. It combines lagged 120-day
    within-family relative return ranks (roll/term-structure proxy), 60/120-day
    trend confirmation, and 60-day volatility sizing with per-symbol/sleeve caps.
    """
    close = _extract_close_history(context)
    close = close[[s for s in SYMBOLS if s in close.columns]].dropna(how="all")
    if len(close) < 121 or close.shape[1] < 10:
        return {s: 0.0 for s in SYMBOLS}

    ret = close.pct_change(fill_method=None)
    r60 = close.pct_change(60, fill_method=None).iloc[-1]
    r120 = close.pct_change(120, fill_method=None).iloc[-1]
    vol = ret.rolling(60, min_periods=40).std().iloc[-1] * math.sqrt(252)

    carry = pd.Series(0.0, index=close.columns)
    for family_symbols in FAMILIES.values():
        available = [s for s in family_symbols if s in close.columns and pd.notna(r120.get(s))]
        if len(available) >= 2:
            carry.loc[available] = r120.loc[available].rank(pct=True) - 0.5

    trend_confirm = ((r60.fillna(-9) > 0).astype(float) + (r120.fillna(-9) > 0).astype(float)) / 2
    trend_score = (r60.rank(pct=True) - 0.5).fillna(0) * 0.5 + (r120.rank(pct=True) - 0.5).fillna(0) * 0.5
    combined = (0.6 * carry + 0.4 * trend_score).where((carry > 0) & (trend_confirm >= 0.5), 0.0)
    invvol = (0.20 / vol).replace([float("inf"), -float("inf")], 0).clip(upper=2).fillna(0)
    raw = combined.clip(lower=0) * invvol
    weights = _cap_weights(raw.reindex(close.columns))
    weight_map = {str(k): float(v) for k, v in weights.to_dict().items()}
    return {s: round(weight_map.get(s, 0.0), 10) for s in SYMBOLS}
