"""Lambda analyzer — disparada por DynamoDB Streams de la tabla operations.

Por cada nuevo item KPI evalúa reglas de anomalía; si detecta una, pide a
Bedrock (Claude Haiku 4.5) un análisis en lenguaje natural con recomendación y
emite una alerta estructurada. La publicación a SNS se cablea en Semana 3.
"""

from __future__ import annotations

from typing import Any

from boto3.dynamodb.types import TypeDeserializer

import bedrock_client
from anomalies import evaluate
from bedrock_client import BedrockError
from logging_utils import log
from prompts import PROMPT_VERSION, build_bedrock_body

_deserializer = TypeDeserializer()


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
