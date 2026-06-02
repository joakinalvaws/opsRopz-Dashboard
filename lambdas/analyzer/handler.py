"""Lambda analyzer — disparada por DynamoDB Streams de la tabla operations.

Por cada nuevo item KPI evalúa reglas de anomalía; si detecta una, pide a
Bedrock (Claude Haiku 4.5) un análisis en lenguaje natural con recomendación y
publica la alerta al topic SNS ops-alerts para su enrutamiento por n8n.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

import boto3
from boto3.dynamodb.types import TypeDeserializer

import bedrock_client
from anomalies import evaluate
from bedrock_client import BedrockError
from logging_utils import log
from prompts import PROMPT_VERSION, build_bedrock_body

_deserializer = TypeDeserializer()
_SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN", "")
_sns_client = None


def _get_sns():
    global _sns_client
    if _sns_client is None:
        _sns_client = boto3.client("sns")
    return _sns_client


def _publish_alert(item: dict[str, Any], anomaly, analysis: str) -> None:
    """Publica la alerta al topic SNS. No-op si SNS_TOPIC_ARN no está configurado."""
    if not _SNS_TOPIC_ARN:
        return
    message = {
        "correlation_id": item.get("correlation_id"),
        "sku": item.get("sku"),
        "severity": anomaly.severity,
        "rule": anomaly.rule,
        "analysis": analysis,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    subject = f"[OpsRopz] {anomaly.severity.upper()}: {anomaly.rule}"[:100]
    try:
        _get_sns().publish(
            TopicArn=_SNS_TOPIC_ARN,
            Subject=subject,
            Message=json.dumps(message, ensure_ascii=False),
        )
    except Exception as exc:  # noqa: BLE001
        log("ERROR", "sns_publish_failed", correlation_id=item.get("correlation_id"), error=str(exc))


def _deserialize(image: dict[str, Any]) -> dict[str, Any]:
    return {k: _deserializer.deserialize(v) for k, v in image.items()}


def _process_record(record: dict[str, Any]) -> None:
    image = record.get("dynamodb", {}).get("NewImage")
    if not image:
        return  # REMOVE u otros sin imagen nueva: nada que analizar

    item = _deserialize(image)
    anomaly = evaluate(item)
    if anomaly is None:
        return

    body = build_bedrock_body(item, anomaly.detail)
    try:
        analysis = bedrock_client.invoke(body)
    except BedrockError as exc:
        # Degradación elegante: la anomalía se detectó, pero falló la explicación.
        # No se reintenta vía stream (evita loops costosos); el fallback LLM en VPS
        # cubre esto en Semana 3.
        log(
            "ERROR",
            "analysis_failed",
            correlation_id=item.get("correlation_id"),
            sku=item.get("sku"),
            severity=anomaly.severity,
            error=str(exc),
        )
        return

    log(
        "INFO",
        "alert_generated",
        correlation_id=item.get("correlation_id"),
        sku=item.get("sku"),
        severity=anomaly.severity,
        rule=anomaly.rule,
        prompt_version=PROMPT_VERSION,
        analysis=analysis,
    )
    _publish_alert(item, anomaly, analysis)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Entry point del stream. Reporta fallos parciales por SequenceNumber."""
    failures: list[dict[str, str]] = []

    for record in event.get("Records", []):
        seq = record.get("dynamodb", {}).get("SequenceNumber", "unknown")
        try:
            _process_record(record)
        except Exception as exc:  # noqa: BLE001 — fallo inesperado: reintentar vía stream
            log("ERROR", "processing_failed", sequence_number=seq, error=str(exc))
            failures.append({"itemIdentifier": seq})

    return {"batchItemFailures": failures}
