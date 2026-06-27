"""Single-name post-OPEX range-release residual continuation (AR-126).

QFA-compatible research model exposing generate_signals(context) -> dict[str, float].
Uses only completed daily OHLCV bars supplied by qfa/Alpaca plus a deterministic
standard monthly OPEX calendar. Research only; never places orders.
"""

from __future__ import annotations

import calendar
import math
from datetime import date
from typing import Any

import pandas as pd

SECTOR_ETFS = ("XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY")
CONTROLS = ("SPY", "QQQ")

# Fixed broad liquid large-cap universe selected ex ante for data coverage/liquidity;
# no return-based selection in the model. Sector map is coarse GICS proxy for ETF residualization.
SECTOR_MAP = {
    "AAPL":"XLK","MSFT":"XLK","NVDA":"XLK","AVGO":"XLK","ORCL":"XLK","CRM":"XLK","ADBE":"XLK","AMD":"XLK","CSCO":"XLK","ACN":"XLK","INTU":"XLK","IBM":"XLK","QCOM":"XLK","TXN":"XLK","NOW":"XLK","AMAT":"XLK","MU":"XLK","LRCX":"XLK","ADI":"XLK","PANW":"XLK","KLAC":"XLK","SNPS":"XLK","CDNS":"XLK","NXPI":"XLK",
    "GOOGL":"XLC","GOOG":"XLC","META":"XLC","NFLX":"XLC","DIS":"XLC","CMCSA":"XLC","TMUS":"XLC","VZ":"XLC","T":"XLC","CHTR":"XLC",
    "AMZN":"XLY","TSLA":"XLY","HD":"XLY","MCD":"XLY","NKE":"XLY","LOW":"XLY","SBUX":"XLY","TJX":"XLY","BKNG":"XLY","CMG":"XLY","ORLY":"XLY","MAR":"XLY","GM":"XLY","F":"XLY",
    "JPM":"XLF","BAC":"XLF","WFC":"XLF","GS":"XLF","MS":"XLF","C":"XLF","AXP":"XLF","BLK":"XLF","SCHW":"XLF","PGR":"XLF","CB":"XLF","MMC":"XLF","ICE":"XLF","CME":"XLF","USB":"XLF","PNC":"XLF",
    "LLY":"XLV","UNH":"XLV","JNJ":"XLV","ABBV":"XLV","MRK":"XLV","TMO":"XLV","ABT":"XLV","DHR":"XLV","PFE":"XLV","ISRG":"XLV","AMGN":"XLV","GILD":"XLV","VRTX":"XLV","REGN":"XLV","SYK":"XLV","MDT":"XLV","BMY":"XLV","CVS":"XLV","CI":"XLV","HUM":"XLV",
    "XOM":"XLE","CVX":"XLE","COP":"XLE","SLB":"XLE","EOG":"XLE","MPC":"XLE","PSX":"XLE","VLO":"XLE","OXY":"XLE","KMI":"XLE",
    "CAT":"XLI","GE":"XLI","HON":"XLI","UNP":"XLI","UPS":"XLI","RTX":"XLI","BA":"XLI","DE":"XLI","LMT":"XLI","ETN":"XLI","ADP":"XLI","MMM":"XLI","WM":"XLI","FDX":"XLI","EMR":"XLI","ITW":"XLI","CSX":"XLI","NSC":"XLI",
    "PG":"XLP","COST":"XLP","WMT":"XLP","KO":"XLP","PEP":"XLP","PM":"XLP","MO":"XLP","MDLZ":"XLP","CL":"XLP","TGT":"XLP","KMB":"XLP","KR":"XLP","SYY":"XLP","GIS":"XLP",
    "LIN":"XLB","SHW":"XLB","APD":"XLB","ECL":"XLB","FCX":"XLB","NEM":"XLB","DOW":"XLB","DD":"XLB","NUE":"XLB","MLM":"XLB",
    "NEE":"XLU","SO":"XLU","DUK":"XLU","AEP":"XLU","SRE":"XLU","D":"XLU","EXC":"XLU","XEL":"XLU","ED":"XLU","PEG":"XLU",
    "PLD":"XLRE","AMT":"XLRE","EQIX":"XLRE","WELL":"XLRE","SPG":"XLRE","PSA":"XLRE","CCI":"XLRE","O":"XLRE","DLR":"XLRE","VICI":"XLRE",
}
UNIVERSE = tuple(SECTOR_MAP)

class ModelParams:
    pre_opex_days = 5
    compression_norm_days = 60
    muted_resid_norm_days = 60
    compression_ratio_max = 0.75
    muted_resid_ratio_max = 0.75
    confirmation_days_after_opex = 1
    hold_days = 5
    residual_min_abs = 0.001
    vol_window = 20
    min_history = 90
    max_abs_weight = 0.04
    max_sector_gross = 0.30
    min_active_names = 8

PARAMS = ModelParams()

def _third_friday(year: int, month: int) -> date:
    cal = calendar.Calendar(firstweekday=calendar.MONDAY)
    fridays = [d for d in cal.itermonthdates(year, month) if d.month == month and d.weekday() == 4]
    return fridays[2]

def _is_first_session_after_opex(idx: pd.DatetimeIndex, pos: int) -> bool:
    if pos < PARAMS.confirmation_days_after_opex:
        return False
    opex_session = idx[pos - PARAMS.confirmation_days_after_opex]
    nominal = _third_friday(opex_session.year, opex_session.month)
    return opex_session.date() == nominal

def _zero(symbols: list[str]) -> dict[str, float]:
    return {s: 0.0 for s in symbols}

def _cap_and_normalize(raw: dict[str, float], output_symbols: list[str]) -> dict[str, float]:
    clean = {s: float(raw.get(s, 0.0)) for s in output_symbols}
    clean = {s: (w if math.isfinite(w) else 0.0) for s, w in clean.items()}
    for _ in range(4):
        for sector in set(SECTOR_MAP.values()):
            names = [s for s in clean if SECTOR_MAP.get(s) == sector]
            gross = sum(abs(clean[s]) for s in names)
            if gross > PARAMS.max_sector_gross and gross > 0:
                scale = PARAMS.max_sector_gross / gross
                for s in names:
                    clean[s] *= scale
        clean = {s: max(-PARAMS.max_abs_weight, min(PARAMS.max_abs_weight, w)) for s, w in clean.items()}
        gross = sum(abs(w) for w in clean.values())
        if gross <= 0:
            return _zero(output_symbols)
        clean = {s: w / gross for s, w in clean.items()}
    return clean

def generate_signals(context: Any) -> dict[str, float]:
    output_symbols = list(context.symbols)
    symbols = [s for s in output_symbols if s in UNIVERSE]
    needed = symbols + [s for s in SECTOR_ETFS if s in output_symbols]
    if not symbols or context.prices.empty:
        return _zero(output_symbols)
    px = context.prices[context.prices["symbol"].isin(needed)].copy()
    px["timestamp"] = pd.to_datetime(px["timestamp"], utc=True)
    px = px.sort_values(["timestamp", "symbol"])
    close = px.pivot(index="timestamp", columns="symbol", values="close").sort_index().ffill()
    high = px.pivot(index="timestamp", columns="symbol", values="high").sort_index().ffill()
    low = px.pivot(index="timestamp", columns="symbol", values="low").sort_index().ffill()
    if len(close) < PARAMS.min_history or close.empty:
        return _zero(output_symbols)
    pos = len(close.index) - 1
    if not _is_first_session_after_opex(close.index, pos):
        return _zero(output_symbols)
    returns = close.pct_change()
    range_pct = ((high - low) / close).replace([float("inf"), float("-inf")], pd.NA)
    pre_range = range_pct.shift(1).rolling(PARAMS.pre_opex_days, min_periods=PARAMS.pre_opex_days).mean()
    base_range = range_pct.shift(PARAMS.pre_opex_days + 1).rolling(PARAMS.compression_norm_days, min_periods=PARAMS.compression_norm_days).median()
    compression = pre_range / base_range.replace(0.0, pd.NA)
    raw: dict[str, float] = {s: 0.0 for s in output_symbols}
    latest = close.index[-1]
    opex_day = close.index[-1 - PARAMS.confirmation_days_after_opex]
    for s in symbols:
        etf = SECTOR_MAP.get(s)
        if s not in close.columns or etf not in close.columns:
            continue
        resid = returns[s] - returns[etf]
        pre_abs = resid.shift(1).abs().rolling(PARAMS.pre_opex_days, min_periods=PARAMS.pre_opex_days).mean()
        base_abs = resid.shift(PARAMS.pre_opex_days + 1).abs().rolling(PARAMS.muted_resid_norm_days, min_periods=PARAMS.muted_resid_norm_days).median()
        muted = pre_abs / base_abs.replace(0.0, pd.NA)
        comp = compression.at[opex_day, s] if opex_day in compression.index else pd.NA
        mute = muted.at[opex_day] if opex_day in muted.index else pd.NA
        conf = resid.at[latest] if latest in resid.index else pd.NA
        vol = resid.shift(1).rolling(PARAMS.vol_window, min_periods=PARAMS.vol_window).std().at[latest]
        if pd.isna(comp) or pd.isna(mute) or pd.isna(conf) or pd.isna(vol):
            continue
        if float(comp) <= PARAMS.compression_ratio_max and float(mute) <= PARAMS.muted_resid_ratio_max and abs(float(conf)) >= PARAMS.residual_min_abs and float(vol) > 0:
            score = (PARAMS.compression_ratio_max - float(comp)) * (PARAMS.muted_resid_ratio_max - float(mute)) * float(conf) / max(float(vol), 0.004)
            raw[s] = score
    if sum(1 for v in raw.values() if abs(v) > 0) < PARAMS.min_active_names:
        return _zero(output_symbols)
    return _cap_and_normalize(raw, output_symbols)
