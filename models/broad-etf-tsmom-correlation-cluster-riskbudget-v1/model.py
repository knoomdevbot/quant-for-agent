"""AR-104 broad ETF TSMOM with rolling-correlation cluster risk budgets.

QFA contract: expose generate_signals(context) -> dict[str, float].
Consumes only market bars supplied by qfa/Alpaca at runtime. Long-only ETF
allocator; gross <= 1, no leverage, no orders.
"""
from __future__ import annotations

import math
from collections import defaultdict, deque
from typing import Dict, Iterable

import pandas as pd

UNIVERSE = (
    "SPY", "QQQ", "IWM", "DIA",
    "XLK", "XLY", "XLI", "XLF", "XLE", "XLB", "XLV", "XLP", "XLU", "XLRE",
    "TLT", "IEF", "SHY", "TIP", "LQD", "HYG",
    "GLD", "SLV", "USO", "DBC", "DBA", "UUP", "FXE", "FXY",
)
SLEEVES = {
    "SPY": "broad_equity", "QQQ": "broad_equity", "IWM": "broad_equity", "DIA": "broad_equity",
    "XLK": "sector_equity", "XLY": "sector_equity", "XLI": "sector_equity", "XLF": "sector_equity",
    "XLE": "sector_equity", "XLB": "sector_equity", "XLV": "defensive_equity", "XLP": "defensive_equity",
    "XLU": "defensive_equity", "XLRE": "rate_sensitive_equity",
    "TLT": "duration", "IEF": "duration", "SHY": "cash_duration", "TIP": "inflation_linked",
    "LQD": "credit", "HYG": "credit",
    "GLD": "precious", "SLV": "precious", "USO": "commodity", "DBC": "commodity", "DBA": "commodity",
    "UUP": "currency", "FXE": "currency", "FXY": "currency",
}
CLUSTER_CAPS = {
    "risk_on_equity": 0.34,
    "defensive_equity": 0.22,
    "rates_credit": 0.34,
    "real_assets": 0.28,
    "currency_defensive": 0.20,
    "uncategorized": 0.18,
}
BASE_CLUSTER = {
    "SPY": "risk_on_equity", "QQQ": "risk_on_equity", "IWM": "risk_on_equity", "DIA": "risk_on_equity",
    "XLK": "risk_on_equity", "XLY": "risk_on_equity", "XLI": "risk_on_equity", "XLF": "risk_on_equity",
    "XLE": "real_assets", "XLB": "real_assets", "XLV": "defensive_equity", "XLP": "defensive_equity",
    "XLU": "defensive_equity", "XLRE": "rates_credit",
    "TLT": "rates_credit", "IEF": "rates_credit", "SHY": "rates_credit", "TIP": "rates_credit",
    "LQD": "rates_credit", "HYG": "risk_on_equity",
    "GLD": "real_assets", "SLV": "real_assets", "USO": "real_assets", "DBC": "real_assets", "DBA": "real_assets",
    "UUP": "currency_defensive", "FXE": "currency_defensive", "FXY": "currency_defensive",
}
LOOKBACKS = (63, 126, 189)
VOL_WINDOW = 63
CORR_WINDOW = 126
MIN_HISTORY = 210
TARGET_VOL = 0.10
MAX_SINGLE = 0.16
MAX_GROSS = 0.98
CORR_LINK_THRESHOLD = 0.72


def _safe(x: float, default: float = 0.0) -> float:
    try:
        y = float(x)
    except Exception:
        return default
    return y if math.isfinite(y) else default


def _ret(close: pd.DataFrame, symbol: str, n: int) -> float:
    if symbol not in close.columns:
        return 0.0
    s = close[symbol].dropna()
    if len(s) <= n or s.iloc[-n - 1] <= 0:
        return 0.0
    return _safe(s.iloc[-1] / s.iloc[-n - 1] - 1.0)


def _vol(close: pd.DataFrame, symbol: str, n: int = VOL_WINDOW) -> float:
    if symbol not in close.columns:
        return TARGET_VOL
    s = close[symbol].dropna()
    if len(s) <= n:
        return TARGET_VOL
    v = _safe(s.pct_change().dropna().tail(n).std(ddof=1) * math.sqrt(252.0), TARGET_VOL)
    return max(v, 0.015)


def _drawdown(close: pd.DataFrame, proxy: str = "SPY", n: int = 126) -> float:
    s = close[proxy].dropna().tail(n) if proxy in close.columns else pd.Series(dtype=float)
    if len(s) < 2:
        return 0.0
    return _safe((s.iloc[-1] / s.cummax().iloc[-1]) - 1.0)


def _connected_components(edges: Dict[str, set[str]], nodes: Iterable[str]) -> list[set[str]]:
    remaining = set(nodes)
    comps: list[set[str]] = []
    while remaining:
        start = remaining.pop()
        comp = {start}
        q = deque([start])
        while q:
            node = q.popleft()
            for nb in edges.get(node, set()):
                if nb in remaining:
                    remaining.remove(nb)
                    comp.add(nb)
                    q.append(nb)
        comps.append(comp)
    return comps


def _rolling_clusters(close: pd.DataFrame, available: list[str]) -> Dict[str, str]:
    # Ex-ante sleeve labels are the fallback. Rolling realized correlations only
    # merge highly similar ETFs into tighter risk-budget buckets.
    rets = close[available].pct_change().dropna(how="all").tail(CORR_WINDOW)
    if len(rets) < 45:
        return {s: BASE_CLUSTER.get(s, "uncategorized") for s in available}
    corr = rets.corr().fillna(0.0)
    edges: Dict[str, set[str]] = defaultdict(set)
    for i, a in enumerate(available):
        for b in available[i + 1:]:
            same_macro = BASE_CLUSTER.get(a, "") == BASE_CLUSTER.get(b, "")
            link_level = 0.68 if same_macro else CORR_LINK_THRESHOLD
            if _safe(corr.loc[a, b]) >= link_level:
                edges[a].add(b)
                edges[b].add(a)
    labels: Dict[str, str] = {}
    for comp in _connected_components(edges, available):
        macro_votes: Dict[str, int] = defaultdict(int)
        for s in comp:
            macro_votes[BASE_CLUSTER.get(s, "uncategorized")] += 1
        macro = max(macro_votes.items(), key=lambda kv: kv[1])[0]
        suffix = "_".join(sorted(comp)[:3])
        for s in comp:
            labels[s] = f"{macro}:{suffix}"
    return labels


def _budget_cap(cluster_label: str) -> float:
    macro = cluster_label.split(":", 1)[0]
    return CLUSTER_CAPS.get(macro, CLUSTER_CAPS["uncategorized"])


def _apply_cluster_caps(weights: Dict[str, float], clusters: Dict[str, str]) -> Dict[str, float]:
    out = dict(weights)
    for _ in range(4):
        cluster_gross: Dict[str, float] = defaultdict(float)
        for s, w in out.items():
            cluster_gross[clusters.get(s, "uncategorized")] += abs(w)
        changed = False
        for label, gross in cluster_gross.items():
            cap = _budget_cap(label)
            if gross > cap > 0:
                scale = cap / gross
                for s in out:
                    if clusters.get(s, "uncategorized") == label:
                        out[s] *= scale
                changed = True
        if not changed:
            break
    return out


def generate_signals(context) -> dict[str, float]:
    symbols = list(getattr(context, "symbols", []) or [])
    weights = {s: 0.0 for s in symbols}
    prices = getattr(context, "prices", None)
    if prices is None or prices.empty:
        return weights
    px = prices.copy()
    px["timestamp"] = pd.to_datetime(px["timestamp"], utc=True)
    close = px[px["symbol"].isin(symbols)].pivot(index="timestamp", columns="symbol", values="close").sort_index().ffill()
    if len(close) < MIN_HISTORY:
        return weights
    available = [s for s in symbols if s in UNIVERSE and s in close.columns and close[s].dropna().shape[0] >= MIN_HISTORY]
    if len(available) < 10:
        return weights

    risk_dd = _drawdown(close, "SPY", 126)
    taper = 1.0
    if risk_dd < -0.18:
        taper = 0.55
    elif risk_dd < -0.10:
        taper = 0.75

    raw: Dict[str, float] = {}
    for s in available:
        mom = 0.50 * _ret(close, s, LOOKBACKS[0]) + 0.35 * _ret(close, s, LOOKBACKS[1]) + 0.15 * _ret(close, s, LOOKBACKS[2])
        if mom <= 0.0:
            raw[s] = 0.0
            continue
        vol_scalar = min(2.5, TARGET_VOL / _vol(close, s, VOL_WINDOW))
        # Mild preference for TSMOM strength without forcing high beta concentration.
        raw[s] = max(0.0, mom) * vol_scalar

    total = sum(raw.values())
    if total <= 1e-12:
        return weights
    w = {s: min(MAX_SINGLE, MAX_GROSS * taper * raw[s] / total) for s in available}
    clusters = _rolling_clusters(close, available)
    w = _apply_cluster_caps(w, clusters)
    gross = sum(abs(v) for v in w.values())
    if gross > MAX_GROSS * taper:
        scale = (MAX_GROSS * taper) / gross
        w = {s: v * scale for s, v in w.items()}
    weights.update({s: _safe(w.get(s, 0.0)) for s in available})
    return weights
