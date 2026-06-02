"""Test de integración del pipeline Semana 1: simulador → SQS → processor → DynamoDB.

Todo con AWS mockeado (moto). No requiere credenciales ni recursos reales.
"""

import os
import random
import sys

import boto3
import pytest
from moto import mock_aws

_PROCESSOR_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SIMULATOR_DIR = os.path.join(_PROCESSOR_DIR, "..", "..", "vps", "simulator")
sys.path.insert(0, _PROCESSOR_DIR)
sys.path.insert(0, os.path.abspath(_SIMULATOR_DIR))

TABLE_NAME = "opsropz-operations-integ"


def _sqs_records(messages):
    """Convierte mensajes recibidos de SQS al formato de evento Lambda."""
    return {"Records": [{"messageId": m["MessageId"], "body": m["Body"]} for m in messages]}


@pytest.fixture
def aws():
    with mock_aws():
        os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
        os.environ["OPERATIONS_TABLE"] = TABLE_NAME

        sqs = boto3.client("sqs", region_name="us-east-1")
        queue_url = sqs.create_queue(QueueName="opsropz-events-integ")["QueueUrl"]

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

        import handler

        handler._table = None
        handler._TABLE_NAME = TABLE_NAME
        yield {"sqs": sqs, "queue_url": queue_url, "table": ddb.Table(TABLE_NAME)}


def test_simulator_to_dynamo_end_to_end(aws):
    import handler
    import main as simulator

    # 1) Simulador genera eventos y los envía a SQS (con semilla → determinista).
    events = simulator.generate_batch(5, random.Random(2026))
    sent = simulator.send_batch(events, aws["sqs"], aws["queue_url"])
    assert sent == 5

    # 2) Drenar la cola como lo haría el event source mapping de Lambda.
    received = (
        aws["sqs"]
        .receive_message(QueueUrl=aws["queue_url"], MaxNumberOfMessages=10)
        .get("Messages", [])
    )
    assert len(received) == 5

    # 3) El processor consume el batch y persiste en DynamoDB.
    result = handler.lambda_handler(_sqs_records(received), None)
    assert result["batchItemFailures"] == []

    stored = aws["table"].scan()["Items"]
    assert len(stored) == 5
    # Todo item conserva su correlation_id (trazabilidad end-to-end).
    assert all(item.get("correlation_id") for item in stored)
