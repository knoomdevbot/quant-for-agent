from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

COMMON_STOCK_TYPES = {"common_stock", "common stock", "cs", "stock"}


@dataclass(frozen=True)
class UniverseConfig:
    as_of: str
    security_master_csv: str
    exchanges: list[str] | None = None
    common_stock_only: bool = True
    include_unknown_classification: bool = False


def _clean_optional_string(value: Any) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _parse_bool(value: Any) -> bool | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y"}:
        return True
    if text in {"0", "false", "no", "n"}:
        return False
    return None


def _timestamp_or_none(value: Any) -> pd.Timestamp | None:
    if value is None:
        return None
    timestamp = pd.Timestamp(value)
    if pd.isna(timestamp):
        return None
    return pd.Timestamp(timestamp)


def _normalize_security_type(value: Any) -> str | None:
    text = _clean_optional_string(value)
    return text.lower().replace("-", "_").replace(" ", "_") if text else None


def load_security_master_csv(path: str | Path) -> pd.DataFrame:
    securities = pd.read_csv(path)
    required = {"symbol"}
    missing = sorted(required - set(securities.columns))
    if missing:
        raise ValueError(f"Security master CSV missing required columns: {', '.join(missing)}")
    securities = securities.copy()
    securities["symbol"] = securities["symbol"].map(lambda value: (_clean_optional_string(value) or "").upper())
    if "listing_date" in securities.columns:
        securities["listing_date"] = pd.to_datetime(securities["listing_date"], utc=True, errors="coerce")
    if "delisting_date" in securities.columns:
        securities["delisting_date"] = pd.to_datetime(securities["delisting_date"], utc=True, errors="coerce")
    return securities


def build_equity_universe(config: UniverseConfig) -> dict[str, Any]:
    securities = load_security_master_csv(config.security_master_csv)
    as_of = pd.Timestamp(config.as_of, tz="UTC")
    exclusions: list[dict[str, str]] = []
    selected: list[str] = []
    allowed_exchanges = {exchange.strip().upper() for exchange in config.exchanges or [] if exchange.strip()}

    has_listing_dates = "listing_date" in securities.columns
    has_delisting_dates = "delisting_date" in securities.columns
    has_security_type = "security_type" in securities.columns

    for row in securities.to_dict("records"):
        symbol = row["symbol"]
        if not symbol:
            exclusions.append({"symbol": "", "reason": "missing_symbol"})
            continue
        exchange = (_clean_optional_string(row.get("exchange")) or "").upper()
        if allowed_exchanges and exchange not in allowed_exchanges:
            exclusions.append({"symbol": symbol, "reason": "exchange_filter"})
            continue
        if has_listing_dates:
            listing_date = _timestamp_or_none(row.get("listing_date"))
            if listing_date is not None and listing_date > as_of:
                exclusions.append({"symbol": symbol, "reason": "not_yet_listed"})
                continue
        if has_delisting_dates:
            delisting_date = _timestamp_or_none(row.get("delisting_date"))
            if delisting_date is not None and delisting_date < as_of:
                exclusions.append({"symbol": symbol, "reason": "delisted_before_as_of"})
                continue
        if config.common_stock_only:
            security_type = _normalize_security_type(row.get("security_type")) if has_security_type else None
            if security_type is None:
                if not config.include_unknown_classification:
                    exclusions.append({"symbol": symbol, "reason": "unknown_security_type"})
                    continue
            elif security_type not in COMMON_STOCK_TYPES:
                exclusions.append({"symbol": symbol, "reason": f"non_common_stock:{security_type}"})
                continue
        selected.append(symbol)

    selected = sorted(dict.fromkeys(selected))
    exclusion_counts: dict[str, int] = {}
    for item in exclusions:
        exclusion_counts[item["reason"]] = exclusion_counts.get(item["reason"], 0) + 1

    point_in_time = has_listing_dates and has_delisting_dates
    warnings: list[str] = []
    if not point_in_time:
        warnings.append(
            "Security master must include both listing_date and delisting_date columns to be treated as point-in-time historical coverage; output is a current/proxy universe."
        )
    if config.common_stock_only and not has_security_type:
        warnings.append(
            "Security master has no security_type column; common-stock filtering depends on include_unknown_classification."
        )

    return {
        "symbols": selected,
        "as_of": config.as_of,
        "point_in_time_universe": point_in_time,
        "universe_spec": {
            "provider": "csv_security_master",
            "security_master_csv": str(Path(config.security_master_csv).expanduser().resolve()),
            "as_of": config.as_of,
            "exchanges": sorted(allowed_exchanges),
            "common_stock_only": config.common_stock_only,
            "include_unknown_classification": config.include_unknown_classification,
        },
        "diagnostics": {
            "input_rows": int(len(securities)),
            "selected_count": int(len(selected)),
            "excluded_count": int(len(exclusions)),
            "excluded_by_reason": exclusion_counts,
            "classification_available": has_security_type,
            "listing_dates_available": has_listing_dates,
            "delisting_dates_available": has_delisting_dates,
            "warnings": warnings,
        },
        "excluded": exclusions,
    }
