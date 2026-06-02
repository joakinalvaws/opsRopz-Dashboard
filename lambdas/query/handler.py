"""Lambda query — expone KPIs y alertas al dashboard vía API Gateway.

Rutas (REST API Gateway con API key + rate limiting):
  GET /kpis    → KPIs actuales por SKU (último snapshot de inventario, ventas 24h)
  GET /alerts  → historial de alertas recientes (tabla alerts, orden temporal)

Funciones de lectura puras sobre DynamoDB. No escribe nada.
"""

from __future__ import annotations

import json
import os
from decimal import Decimal
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key
from logging_utils import log

_OPERATIONS_TABLE = os.environ.get("OPERATIONS_TABLE", "")
_ALERTS_TABLE = os.environ.get("ALERTS_TABLE", "")
_ALERT_PARTITION = "ALERT"
_ALERTS_LIMIT = 50

_dynamo = None


def _get_dynamo():
    global _dynamo
    if _dynamo is None:
        _dynamo = boto3.resource("dynamodb")
    return _dynamo


def _to_jsonable(obj: Any) -> Any:
    """DynamoDB devuelve Decimal; conviértelo a int/float para serializar a JSON."""
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_jsonable(v) for v in obj]
    return obj


def _response(status: int, body: Any) -> dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            # CORS: el dashboard llama vía su backend (server-side), pero se deja
            # abierto para flexibilidad. La API key protege el acceso real.
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(_to_jsonable(body), ensure_ascii=False),
    }


def _get_kpis() -> dict[str, Any]:
    """Último snapshot de inventario por SKU + conteo de ventas, desde operations."""
    table = _get_dynamo().Table(_OPERATIONS_TABLE)
    items: list[dict] = []
    response = table.scan()
    items.extend(response.get("Items", []))
    while "LastEvaluatedKey" in response:
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        items.extend(response.get("Items", []))

    # Último snapshot de inventario por SKU (event_id arranca con el timestamp,
    # así que el máximo lexicográfico es el más reciente).
    latest_inventory: dict[str, dict] = {}
    sales_count = 0
    for it in items:
        etype = it.get("event_type")
        if etype == "inventory_snapshot":
            sku = it.get("sku")
            prev = latest_inventory.get(sku)
            if prev is None or it.get("event_id", "") > prev.get("event_id", ""):
                latest_inventory[sku] = it
        elif etype == "sale":
            sales_count += 1

    inventory = [
        {
            "sku": v.get("sku"),
            "days_of_stock": v.get("days_of_stock"),
            "current_stock": v.get("current_stock"),
            "store_id": v.get("store_id"),
            "timestamp": v.get("timestamp"),
        }
        for v in latest_inventory.values()
    ]
    inventory.sort(key=lambda x: (x["days_of_stock"] is None, x["days_of_stock"]))

    critical = [i for i in inventory if i["days_of_stock"] is not None and i["days_of_stock"] < 3]

    return {
        "skus_tracked": len(inventory),
        "critical_count": len(critical),
        "sales_events": sales_count,
        "inventory": inventory,
    }


def _get_alerts() -> dict[str, Any]:
    """Alertas recientes ordenadas de más nueva a más vieja."""
    if not _ALERTS_TABLE:
        return {"alerts": []}
    table = _get_dynamo().Table(_ALERTS_TABLE)
    response = table.query(
        KeyConditionExpression=Key("alert_partition").eq(_ALERT_PARTITION),
        ScanIndexForward=False,  # descendente: más recientes primero
        Limit=_ALERTS_LIMIT,
    )
    alerts = [
        {
            "sku": a.get("sku"),
            "severity": a.get("severity"),
            "rule": a.get("rule"),
            "analysis": a.get("analysis"),
            "correlation_id": a.get("correlation_id"),
            "created_at": a.get("created_at"),
        }
        for a in response.get("Items", [])
    ]
    return {"alerts": alerts}


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    path = event.get("path") or event.get("resource") or ""
    try:
        if path.endswith("/kpis"):
            return _response(200, _get_kpis())
        if path.endswith("/alerts"):
            return _response(200, _get_alerts())
        return _response(404, {"error": "not_found", "path": path})
    except Exception as exc:
        log("ERROR", "query_failed", path=path, error=str(exc))
        return _response(500, {"error": "internal_error"})
