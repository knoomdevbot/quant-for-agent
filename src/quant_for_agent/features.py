from __future__ import annotations

import csv
import json
import math
import os
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Protocol

from .config import DEFAULT_DB_PATH

FEATURE_SCHEMA = """
CREATE TABLE IF NOT EXISTS feature_observations (
  feature_name TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  value REAL NOT NULL,
  metadata_json TEXT NOT NULL DEFAULT '{}',
  source TEXT,
  created_at TEXT NOT NULL,
  PRIMARY KEY (feature_name, entity_id, timestamp)
);

CREATE INDEX IF NOT EXISTS idx_feature_observations_feature_timestamp
ON feature_observations (feature_name, timestamp);
"""

DEFAULT_FEATURE_TABLE = "qfa-feature-observations"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_timestamp(value: str) -> str:
    text = value.strip()
    if not text:
        raise ValueError("timestamp is required")
    if len(text) == 10 and text[4] == "-" and text[7] == "-":
        return text
    normalized = text.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalized)
    except ValueError:
        return text
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt.isoformat(timespec="seconds") + ("Z" if "T" in dt.isoformat() else "")


def _require_nonempty(value: str, field_name: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} is required")
    if "#" in cleaned:
        raise ValueError(f"{field_name} cannot contain '#'")
    return cleaned


@dataclass(frozen=True)
class FeatureObservation:
    feature_name: str
    entity_id: str
    timestamp: str
    value: float
    metadata: dict[str, Any] = field(default_factory=dict)
    source: str | None = None
    created_at: str = field(default_factory=utc_now_iso)

    def __post_init__(self) -> None:
        object.__setattr__(self, "feature_name", _require_nonempty(self.feature_name, "feature_name"))
        object.__setattr__(self, "entity_id", _require_nonempty(self.entity_id, "entity_id"))
        object.__setattr__(self, "timestamp", normalize_timestamp(self.timestamp))
        finite_value = float(self.value)
        if not math.isfinite(finite_value):
            raise ValueError("value must be finite")
        object.__setattr__(self, "value", finite_value)
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be a JSON object")
        if self.source is not None and not self.source.strip():
            object.__setattr__(self, "source", None)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class FeatureStore(Protocol):
    def put(self, observation: FeatureObservation) -> FeatureObservation: ...

    def get(self, feature_name: str, entity_id: str, timestamp: str) -> FeatureObservation | None: ...

    def query(
        self,
        feature_name: str,
        entity_id: str | None = None,
        start: str | None = None,
        end: str | None = None,
        limit: int = 100,
    ) -> list[FeatureObservation]: ...


class SQLiteFeatureStore:
    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(FEATURE_SCHEMA)
        self.conn.commit()

    def put(self, observation: FeatureObservation) -> FeatureObservation:
        self.conn.execute(
            """
            INSERT INTO feature_observations
              (feature_name, entity_id, timestamp, value, metadata_json, source, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(feature_name, entity_id, timestamp) DO UPDATE SET
              value=excluded.value,
              metadata_json=excluded.metadata_json,
              source=excluded.source,
              created_at=excluded.created_at
            """,
            (
                observation.feature_name,
                observation.entity_id,
                observation.timestamp,
                observation.value,
                json.dumps(observation.metadata, sort_keys=True),
                observation.source,
                observation.created_at,
            ),
        )
        self.conn.commit()
        return observation

    def get(self, feature_name: str, entity_id: str, timestamp: str) -> FeatureObservation | None:
        row = self.conn.execute(
            """
            SELECT * FROM feature_observations
            WHERE feature_name = ? AND entity_id = ? AND timestamp = ?
            """,
            (feature_name, entity_id, normalize_timestamp(timestamp)),
        ).fetchone()
        return self._decode(row) if row else None

    def query(
        self,
        feature_name: str,
        entity_id: str | None = None,
        start: str | None = None,
        end: str | None = None,
        limit: int = 100,
    ) -> list[FeatureObservation]:
        filters = ["feature_name = ?"]
        params: list[Any] = [feature_name]
        if entity_id is not None:
            filters.append("entity_id = ?")
            params.append(entity_id)
        if start is not None:
            filters.append("timestamp >= ?")
            params.append(normalize_timestamp(start))
        if end is not None:
            filters.append("timestamp <= ?")
            params.append(normalize_timestamp(end))
        params.append(limit)
        rows = self.conn.execute(
            f"""
            SELECT * FROM feature_observations
            WHERE {' AND '.join(filters)}
            ORDER BY timestamp, entity_id
            LIMIT ?
            """,
            params,
        ).fetchall()
        return [self._decode(row) for row in rows]

    @staticmethod
    def _decode(row: sqlite3.Row) -> FeatureObservation:
        return FeatureObservation(
            feature_name=row["feature_name"],
            entity_id=row["entity_id"],
            timestamp=row["timestamp"],
            value=float(row["value"]),
            metadata=json.loads(row["metadata_json"] or "{}"),
            source=row["source"],
            created_at=row["created_at"],
        )


class DynamoDBFeatureStore:
    def __init__(self, table_name: str = DEFAULT_FEATURE_TABLE, region_name: str | None = None, client=None):
        self.table_name = table_name
        if client is None:
            try:
                import boto3
            except ImportError as exc:
                raise RuntimeError(
                    "DynamoDB feature backend requires boto3. Install qfa with AWS support or add boto3."
                ) from exc
            client = boto3.client("dynamodb", region_name=region_name)
        self.client = client

    def put(self, observation: FeatureObservation) -> FeatureObservation:
        item = self._to_item(observation)
        self.client.put_item(TableName=self.table_name, Item=item)
        return observation

    def get(self, feature_name: str, entity_id: str, timestamp: str) -> FeatureObservation | None:
        response = self.client.get_item(
            TableName=self.table_name,
            Key={
                "feature_entity": {"S": feature_entity_key(feature_name, entity_id)},
                "timestamp": {"S": normalize_timestamp(timestamp)},
            },
        )
        item = response.get("Item")
        return self._from_item(item) if item else None

    def query(
        self,
        feature_name: str,
        entity_id: str | None = None,
        start: str | None = None,
        end: str | None = None,
        limit: int = 100,
    ) -> list[FeatureObservation]:
        expr_names: dict[str, str] = {}
        expr_values: dict[str, dict[str, str]] = {}
        kwargs: dict[str, Any] = {"TableName": self.table_name, "Limit": limit}
        key_conditions: list[str]
        if entity_id is not None:
            expr_values[":feature_entity"] = {"S": feature_entity_key(feature_name, entity_id)}
            key_conditions = ["feature_entity = :feature_entity"]
        else:
            kwargs["IndexName"] = "FeatureTimestampIndex"
            expr_values[":feature_name"] = {"S": feature_name}
            key_conditions = ["feature_name = :feature_name"]
        if start is not None and end is not None:
            expr_names["#ts"] = "timestamp"
            expr_values[":start"] = {"S": normalize_timestamp(start)}
            expr_values[":end"] = {"S": normalize_timestamp(end)}
            key_conditions.append("#ts BETWEEN :start AND :end")
        elif start is not None:
            expr_names["#ts"] = "timestamp"
            expr_values[":start"] = {"S": normalize_timestamp(start)}
            key_conditions.append("#ts >= :start")
        elif end is not None:
            expr_names["#ts"] = "timestamp"
            expr_values[":end"] = {"S": normalize_timestamp(end)}
            key_conditions.append("#ts <= :end")
        kwargs["KeyConditionExpression"] = " AND ".join(key_conditions)
        if expr_names:
            kwargs["ExpressionAttributeNames"] = expr_names
        kwargs["ExpressionAttributeValues"] = expr_values
        items: list[dict[str, dict[str, str]]] = []
        while True:
            response = self.client.query(**kwargs)
            items.extend(response.get("Items", []))
            if len(items) >= limit or "LastEvaluatedKey" not in response:
                break
            kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
            kwargs["Limit"] = limit - len(items)
        observations = [self._from_item(item) for item in items[:limit]]
        return sorted(observations, key=lambda item: (item.timestamp, item.entity_id))

    @staticmethod
    def _to_item(observation: FeatureObservation) -> dict[str, dict[str, str]]:
        return {
            "feature_entity": {"S": feature_entity_key(observation.feature_name, observation.entity_id)},
            "feature_name": {"S": observation.feature_name},
            "entity_id": {"S": observation.entity_id},
            "timestamp": {"S": observation.timestamp},
            "value": {"N": str(Decimal(str(observation.value)))},
            "metadata_json": {"S": json.dumps(observation.metadata, sort_keys=True)},
            "source": {"S": observation.source or ""},
            "created_at": {"S": observation.created_at},
        }

    @staticmethod
    def _from_item(item: dict[str, dict[str, str]]) -> FeatureObservation:
        return FeatureObservation(
            feature_name=item["feature_name"]["S"],
            entity_id=item["entity_id"]["S"],
            timestamp=item["timestamp"]["S"],
            value=float(item["value"]["N"]),
            metadata=json.loads(item.get("metadata_json", {"S": "{}"})["S"] or "{}"),
            source=item.get("source", {"S": ""})["S"] or None,
            created_at=item.get("created_at", {"S": utc_now_iso()})["S"],
        )


def feature_entity_key(feature_name: str, entity_id: str) -> str:
    return f"{feature_name}#{entity_id}"


def parse_metadata_json(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError("metadata JSON must be an object")
    return parsed


def load_observations_csv(path: str | Path) -> list[FeatureObservation]:
    observations: list[FeatureObservation] = []
    with Path(path).expanduser().open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"feature_name", "entity_id", "timestamp", "value"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV missing required columns: {', '.join(sorted(missing))}")
        for row in reader:
            observations.append(
                FeatureObservation(
                    feature_name=row["feature_name"],
                    entity_id=row["entity_id"],
                    timestamp=row["timestamp"],
                    value=float(row["value"]),
                    metadata=parse_metadata_json(row.get("metadata_json") or row.get("metadata")),
                    source=row.get("source") or None,
                )
            )
    return observations


def build_feature_store(
    *,
    backend: str | None = None,
    db_path: str | Path | None = None,
    table_name: str | None = None,
    region_name: str | None = None,
    dynamodb_client=None,
) -> FeatureStore:
    selected = (backend or os.environ.get("QFA_FEATURE_BACKEND") or "sqlite").strip().lower()
    if selected == "sqlite":
        return SQLiteFeatureStore(db_path or DEFAULT_DB_PATH)
    if selected == "dynamodb":
        return DynamoDBFeatureStore(
            table_name=table_name or os.environ.get("QFA_FEATURE_TABLE") or DEFAULT_FEATURE_TABLE,
            region_name=region_name
            or os.environ.get("QFA_AWS_REGION")
            or os.environ.get("AWS_REGION")
            or os.environ.get("AWS_DEFAULT_REGION"),
            client=dynamodb_client,
        )
    raise ValueError("Unsupported feature backend: expected sqlite or dynamodb")
