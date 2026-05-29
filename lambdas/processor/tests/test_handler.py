import json
import os
import sys

import boto3
import pytest
from moto import mock_aws

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TABLE_NAME = "opsropz-operations-test"


def _sqs_event(*bodies):
    return {
        "Records": [
            {"messageId": f"msg-{i}", "body": json.dumps(b)} for i, b in enumerate(bodies)
        ]
    }


def _inventory(corr="c1", sku="LECHE_GLORIA_1L"):
    return {
        "correlation_id": corr,
        "event_type": "inventory_snapshot",
        "timestamp": "2026-05-29T14:30:00Z",
        "store_id": "lima-centro",
        "sku": sku,
        "payload": {"current_stock": 72, "avg_daily_sales": 48.0},
    }


@pytest.fixture
def table():
    with mock_aws():
        os.environ["OPERATIONS_TABLE"] = TABLE_NAME
        os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
        ddb = boto3.resource("dynamodb", region_name="us-east-1")
        ddb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {"AttributeName": "sku", "KeyType": "HASH"},
                {"AttributeName": "event_id", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "sku", "AttributeType": "S"},
                {"AttributeName": "event_id", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        # Reset del estado cacheado del módulo y rebind del nombre de tabla.
        import handler

        handler._table = None
        handler._TABLE_NAME = TABLE_NAME
        yield ddb.Table(TABLE_NAME)


def test_persists_item_with_kpi(table):
    import handler

    result = handler.lambda_handler(_sqs_event(_inventory()), None)

    assert result["batchItemFailures"] == []
    items = table.scan()["Items"]
    assert len(items) == 1
    assert items[0]["sku"] == "LECHE_GLORIA_1L"
    assert float(items[0]["days_of_stock"]) == 1.5
    assert items[0]["correlation_id"] == "c1"


def test_malformed_event_is_dropped_not_retried(table):
    import handler

    bad = {"event_type": "inventory_snapshot"}  # falta correlation_id, sku, timestamp
    result = handler.lambda_handler(_sqs_event(bad), None)

    # No se reintenta (no aparece en failures) y no se persiste nada.
    assert result["batchItemFailures"] == []
    assert table.scan()["Count"] == 0


def test_partial_batch_failure_reports_only_bad_record(table):
    import handler

    invalid_json_record = {"messageId": "broken", "body": "{not json"}
    event = _sqs_event(_inventory())
    event["Records"].append(invalid_json_record)

    result = handler.lambda_handler(event, None)

    failure_ids = [f["itemIdentifier"] for f in result["batchItemFailures"]]
    assert failure_ids == ["broken"]
    assert table.scan()["Count"] == 1


def test_reprocessing_same_event_is_idempotent(table):
    import handler

    event = _sqs_event(_inventory())
    handler.lambda_handler(event, None)
    handler.lambda_handler(event, None)

    # Misma clave (sku, timestamp) → sobrescribe, no duplica.
    assert table.scan()["Count"] == 1
