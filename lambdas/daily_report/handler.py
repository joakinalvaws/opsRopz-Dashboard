"""Lambda daily_report — resumen diario de KPIs enviado por email (SES).

Disparada por EventBridge a las 8am UTC. Escanea los ítems de las últimas 24h
en DynamoDB y envía un resumen por email. También publica en SNS para
visibilidad en Slack (#ops-alertas).
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import boto3
from boto3.dynamodb.conditions import Attr

from logging_utils import log

_TABLE_NAME = os.environ.get("OPERATIONS_TABLE", "opsropz-operations-dev")
_SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN", "")
_SES_SENDER = os.environ.get("SES_SENDER", "")
_SES_RECIPIENT = os.environ.get("SES_RECIPIENT", "")

_dynamo_resource = None
_ses_client = None
_sns_client = None


def _get_dynamo():
    global _dynamo_resource
    if _dynamo_resource is None:
        _dynamo_resource = boto3.resource("dynamodb")
    return _dynamo_resource


def _get_ses():
    global _ses_client
    if _ses_client is None:
        _ses_client = boto3.client("ses")
    return _ses_client


def _get_sns():
    global _sns_client
    if _sns_client is None:
        _sns_client = boto3.client("sns")
    return _sns_client


def _to_float(v: Any) -> float:
    if isinstance(v, Decimal):
        return float(v)
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _scan_last_24h(table) -> list[dict]:
    since = (datetime.now(timezone.utc) - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
    response = table.scan(FilterExpression=Attr("ingested_at").gte(since))
    items = list(response.get("Items", []))
    while "LastEvaluatedKey" in response:
        response = table.scan(
            FilterExpression=Attr("ingested_at").gte(since),
            ExclusiveStartKey=response["LastEvaluatedKey"],
        )
        items.extend(response.get("Items", []))
    return items


def _build_report(items: list[dict], date_str: str) -> str:
    inventory_items = [i for i in items if i.get("event_type") == "inventory_snapshot"]
    sale_items = [i for i in items if i.get("event_type") == "sale"]
    critical_stock = [i for i in inventory_items if _to_float(i.get("days_of_stock", 999)) < 3]
    total_sales = sum(_to_float(i.get("quantity", 0)) for i in sale_items)

    lines = [
        f"Reporte operacional — {date_str}",
        "=" * 42,
        f"Eventos procesados (últimas 24h): {len(items)}",
        f"  • Snapshots de inventario: {len(inventory_items)}",
        f"  • Ventas registradas:       {len(sale_items)}",
        "",
        f"Total unidades vendidas: {int(total_sales)}",
        "",
    ]

    if critical_stock:
        lines.append(f"⚠ STOCK CRÍTICO ({len(critical_stock)} SKU(s)):")
        for item in sorted(critical_stock, key=lambda x: _to_float(x.get("days_of_stock", 0))):
            sku = item["sku"]
            dos = _to_float(item.get("days_of_stock", 0))
            lines.append(f"  • {sku}: {dos:.1f} días de stock restante")
        lines.append("")
    else:
        lines.append("Sin alertas críticas de stock en las últimas 24h.")
        lines.append("")

    lines += ["—", "OpsRopz — Sistema de inteligencia operacional"]
    return "\n".join(lines)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    date_str = datetime.now(timezone.utc).strftime("%d/%m/%Y")
    table = _get_dynamo().Table(_TABLE_NAME)
    items = _scan_last_24h(table)
    body = _build_report(items, date_str)
    subject = f"[OpsRopz] Reporte diario {date_str}"
    critical_count = len([i for i in items if _to_float(i.get("days_of_stock", 999)) < 3])

    if _SES_SENDER and _SES_RECIPIENT:
        _get_ses().send_email(
            Source=_SES_SENDER,
            Destination={"ToAddresses": [_SES_RECIPIENT]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {"Text": {"Data": body, "Charset": "UTF-8"}},
            },
        )
        log("INFO", "email_sent", recipient=_SES_RECIPIENT, eventos=len(items))

    if _SNS_TOPIC_ARN:
        _get_sns().publish(
            TopicArn=_SNS_TOPIC_ARN,
            Subject=subject[:100],
            Message=json.dumps(
                {
                    "correlation_id": "daily_report",
                    "severity": "info",
                    "rule": "reporte_diario",
                    "analysis": body,
                    "eventos_24h": len(items),
                    "stock_critico_count": critical_count,
                },
                ensure_ascii=False,
            ),
        )

    log("INFO", "report_completed", eventos=len(items), stock_critico=critical_count)
    return {"report_sent": True, "eventos_procesados": len(items)}
