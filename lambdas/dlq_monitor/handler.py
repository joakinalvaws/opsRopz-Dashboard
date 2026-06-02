"""Lambda dlq_monitor — verifica la DLQ y publica a SNS si hay mensajes pendientes.

Disparada por EventBridge cada 6 horas. Emite una alerta crítica cuando la DLQ
tiene mensajes, lo que indica eventos que fallaron después de 3 reintentos.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from typing import Any

import boto3
from logging_utils import log

_DLQ_URL = os.environ.get("DLQ_URL", "")
_SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN", "")

_sqs_client = None
_sns_client = None


def _get_sqs():
    global _sqs_client
    if _sqs_client is None:
        _sqs_client = boto3.client("sqs")
    return _sqs_client


def _get_sns():
    global _sns_client
    if _sns_client is None:
        _sns_client = boto3.client("sns")
    return _sns_client


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    attrs = _get_sqs().get_queue_attributes(
        QueueUrl=_DLQ_URL,
        AttributeNames=["ApproximateNumberOfMessages"],
    )
    count = int(attrs["Attributes"]["ApproximateNumberOfMessages"])

    log("INFO", "dlq_checked", dlq_message_count=count)

    if count == 0:
        return {"dlq_messages": 0}

    message = json.dumps(
        {
            "correlation_id": "dlq_monitor",
            "sku": "SISTEMA",
            "severity": "critico",
            "rule": "mensajes_en_dlq",
            "analysis": (
                f"La DLQ tiene {count} mensaje(s) pendiente(s) de análisis. "
                "Revisar CloudWatch Logs del processor para identificar la causa raíz."
            ),
            "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "dlq_count": count,
        },
        ensure_ascii=False,
    )

    _get_sns().publish(
        TopicArn=_SNS_TOPIC_ARN,
        Subject=f"[OpsRopz] CRITICO: {count} mensaje(s) en DLQ"[:100],
        Message=message,
    )

    log("ERROR", "dlq_has_messages", dlq_message_count=count)
    return {"dlq_messages": count}
