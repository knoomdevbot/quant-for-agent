import csv
import json

from typer.testing import CliRunner

from quant_for_agent import cli
from quant_for_agent.features import (
    DynamoDBFeatureStore,
    FeatureObservation,
    SQLiteFeatureStore,
    load_observations_csv,
)


class FakeDynamoDBClient:
    def __init__(self):
        self.items = {}
        self.put_calls = []
        self.query_calls = []

    def put_item(self, **kwargs):
        self.put_calls.append(kwargs)
        item = kwargs["Item"]
        key = (item["feature_entity"]["S"], item["timestamp"]["S"])
        self.items[key] = item
        return {}

    def get_item(self, **kwargs):
        key = (kwargs["Key"]["feature_entity"]["S"], kwargs["Key"]["timestamp"]["S"])
        item = self.items.get(key)
        return {"Item": item} if item else {}

    def query(self, **kwargs):
        self.query_calls.append(kwargs)
        values = kwargs["ExpressionAttributeValues"]
        if ":feature_entity" in values:
            feature_entity = values[":feature_entity"]["S"]
            items = [item for (key, _ts), item in self.items.items() if key == feature_entity]
        else:
            feature_name = values[":feature_name"]["S"]
            items = [item for item in self.items.values() if item["feature_name"]["S"] == feature_name]
        if ":start" in values:
            items = [item for item in items if item["timestamp"]["S"] >= values[":start"]["S"]]
        if ":end" in values:
            items = [item for item in items if item["timestamp"]["S"] <= values[":end"]["S"]]
        return {"Items": sorted(items, key=lambda item: (item["timestamp"]["S"], item["entity_id"]["S"]))}


def test_sqlite_feature_store_put_get_query(tmp_path):
    store = SQLiteFeatureStore(tmp_path / "qfa.sqlite3")
    store.put(
        FeatureObservation(
            feature_name="news.sentiment.industry",
            entity_id="semiconductors",
            timestamp="2026-07-01",
            value=0.42,
            metadata={"keyword": "chips"},
            source="test",
        )
    )
    store.put(
        FeatureObservation(
            feature_name="news.sentiment.industry",
            entity_id="banks",
            timestamp="2026-07-02",
            value=-0.10,
        )
    )

    observation = store.get("news.sentiment.industry", "semiconductors", "2026-07-01")
    assert observation is not None
    assert observation.value == 0.42
    assert observation.metadata == {"keyword": "chips"}
    assert observation.source == "test"

    series = store.query("news.sentiment.industry", start="2026-07-01", end="2026-07-02")
    assert [(item.entity_id, item.timestamp, item.value) for item in series] == [
        ("semiconductors", "2026-07-01", 0.42),
        ("banks", "2026-07-02", -0.10),
    ]


def test_feature_csv_loader(tmp_path):
    csv_path = tmp_path / "features.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["feature_name", "entity_id", "timestamp", "value", "metadata_json", "source"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "feature_name": "news.sentiment.industry",
                "entity_id": "semiconductors",
                "timestamp": "2026-07-01",
                "value": "0.5",
                "metadata_json": '{"sample": 12}',
                "source": "pipeline",
            }
        )

    observations = load_observations_csv(csv_path)

    assert len(observations) == 1
    assert observations[0].metadata == {"sample": 12}
    assert observations[0].source == "pipeline"


def test_dynamodb_feature_store_request_shape():
    client = FakeDynamoDBClient()
    store = DynamoDBFeatureStore(table_name="qfa-feature-observations", region_name="us-west-2", client=client)

    store.put(
        FeatureObservation(
            feature_name="news.sentiment.industry",
            entity_id="semiconductors",
            timestamp="2026-07-01",
            value=0.7,
            metadata={"keyword": "chips"},
            source="unit-test",
        )
    )

    put_call = client.put_calls[0]
    assert put_call["TableName"] == "qfa-feature-observations"
    assert put_call["Item"]["feature_entity"] == {"S": "news.sentiment.industry#semiconductors"}
    assert put_call["Item"]["value"] == {"N": "0.7"}

    fetched = store.get("news.sentiment.industry", "semiconductors", "2026-07-01")
    assert fetched is not None
    assert fetched.value == 0.7
    assert fetched.metadata == {"keyword": "chips"}

    by_feature = store.query("news.sentiment.industry", start="2026-07-01", end="2026-07-02")
    assert len(by_feature) == 1
    assert client.query_calls[-1]["IndexName"] == "FeatureTimestampIndex"

    by_entity_no_range = store.query("news.sentiment.industry", entity_id="semiconductors")
    assert len(by_entity_no_range) == 1
    assert "ExpressionAttributeNames" not in client.query_calls[-1]


def test_feature_observation_rejects_non_finite_values():
    try:
        FeatureObservation(
            feature_name="news.sentiment.industry",
            entity_id="semiconductors",
            timestamp="2026-07-01",
            value=float("nan"),
        )
    except ValueError as exc:
        assert str(exc) == "value must be finite"
    else:
        raise AssertionError("expected non-finite feature value to be rejected")


def test_cli_features_backend_can_come_from_env(monkeypatch, tmp_path):
    monkeypatch.setenv("QFA_FEATURE_BACKEND", "bogus")
    result = CliRunner().invoke(
        cli.app,
        ["features", "query", "--name", "news.sentiment.industry", "--db", str(tmp_path / "qfa.sqlite3")],
    )

    assert result.exit_code == 2
    assert "Unsupported feature backend" in result.output


def test_cli_features_put_get_query_and_import_csv(tmp_path):
    db_path = tmp_path / "qfa.sqlite3"
    runner = CliRunner()

    put_result = runner.invoke(
        cli.app,
        [
            "features",
            "put",
            "--name",
            "news.sentiment.industry",
            "--entity",
            "semiconductors",
            "--timestamp",
            "2026-07-01",
            "--value",
            "0.55",
            "--metadata-json",
            '{"keyword":"chips"}',
            "--source",
            "manual",
            "--db",
            str(db_path),
        ],
    )
    assert put_result.exit_code == 0
    assert json.loads(put_result.output)["observation"]["value"] == 0.55

    get_result = runner.invoke(
        cli.app,
        [
            "features",
            "get",
            "--name",
            "news.sentiment.industry",
            "--entity",
            "semiconductors",
            "--timestamp",
            "2026-07-01",
            "--db",
            str(db_path),
        ],
    )
    assert get_result.exit_code == 0
    assert json.loads(get_result.output)["metadata"] == {"keyword": "chips"}

    csv_path = tmp_path / "features.csv"
    csv_path.write_text(
        "feature_name,entity_id,timestamp,value,metadata_json,source\n"
        'news.sentiment.industry,banks,2026-07-02,-0.2,"{""keyword"":""banks""}",fixture\n',
        encoding="utf-8",
    )
    import_result = runner.invoke(
        cli.app,
        ["features", "import-csv", str(csv_path), "--db", str(db_path)],
    )
    assert import_result.exit_code == 0
    assert json.loads(import_result.output)["count"] == 1

    query_result = runner.invoke(
        cli.app,
        [
            "features",
            "query",
            "--name",
            "news.sentiment.industry",
            "--start",
            "2026-07-01",
            "--end",
            "2026-07-02",
            "--db",
            str(db_path),
        ],
    )
    assert query_result.exit_code == 0
    payload = json.loads(query_result.output)
    assert [(item["entity_id"], item["value"]) for item in payload] == [
        ("semiconductors", 0.55),
        ("banks", -0.2),
    ]
