"""Lambda processor — consume eventos de SQS, calcula KPIs y persiste en DynamoDB.

Disparada por la cola `events`. Usa reporte de fallos parciales de batch
(`batchItemFailures`) para que solo los mensajes que fallan vuelvan a la cola
y, tras 3 reintentos, terminen en la DLQ — sin reprocesar los que sí pasaron.
"""

from __future__ import annotations

import json
import os
from decimal import Decimal
from typing import Any

import boto3
from logging_utils import log
from normalize import InvalidEventError, build_item

_TABLE_NAME = os.environ.get("OPERATIONS_TABLE", "opsropz-operations-dev")
_table = None


def _get_table():
    """Cliente DynamoDB perezoso, cacheado entre invocaciones (warm starts)."""
    global _table
    if _table is None:
        _table = boto3.resource("dynamodb").Table(_TABLE_NAME)
    return _table


def _to_dynamo(item: dict[str, Any]) -> dict[str, Any]:
    """DynamoDB no acepta float vía el resource API; convierte a Decimal."""
    return json.loads(json.dumps(item), parse_float=Decimal)


def _process_record(record: dict[str, Any]) -> None:
    event = json.loads(record["body"])
    item = build_item(event)
    _get_table().put_item(Item=_to_dynamo(item))
    log(
        "INFO",
        "kpi_calculated",
        correlation_id=event.get("correlation_id"),
        sku=item["sku"],
        source_event_type=item["event_type"],
        days_of_stock=item.get("days_of_stock"),
    )


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Punto de entrada SQS. Devuelve los IDs de mensajes que fallaron."""
    failures: list[dict[str, str]] = []

    for record in event.get("Records", []):
        message_id = record.get("messageId", "unknown")
        try:
            _process_record(record)
        except InvalidEventError as exc:
            # Evento malformado: no tiene sentido reintentarlo. Se loguea y se
            # descarta (no se agrega a failures) para que no sature la DLQ.
            log("ERROR", "invalid_event", message_id=message_id, error=str(exc))
        except Exception as exc:
            log("ERROR", "processing_failed", message_id=message_id, error=str(exc))
            failures.append({"itemIdentifier": message_id})

    return {"batchItemFailures": failures}
