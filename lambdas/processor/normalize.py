"""Normalización de eventos retail crudos a items de DynamoDB.

Función pura: recibe el dict del evento, valida el envelope, calcula KPIs
derivados y devuelve el item listo para persistir. Sin I/O.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from kpis import days_of_stock

REQUIRED_FIELDS = ("correlation_id", "event_type", "timestamp", "sku")


class InvalidEventError(ValueError):
    """El evento no cumple el contrato (envelope incompleto)."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_item(event: dict[str, Any]) -> dict[str, Any]:
    """Valida un evento y lo convierte en un item de DynamoDB con KPIs.

    Lanza InvalidEventError si falta algún campo del envelope.
    """
    missing = [f for f in REQUIRED_FIELDS if not event.get(f)]
    if missing:
        raise InvalidEventError(f"Campos faltantes en el evento: {missing}")

    payload = event.get("payload") or {}

    item: dict[str, Any] = {
        "sku": event["sku"],
        # Sort key único por evento: ordena cronológicamente (prefijo timestamp)
        # y evita colisiones entre eventos del mismo SKU en el mismo instante.
        # Reprocesar el mismo evento da el mismo event_id → sobrescribe (idempotente).
        "event_id": f"{event['timestamp']}#{event['correlation_id']}",
        "timestamp": event["timestamp"],
        "event_type": event["event_type"],
        "store_id": event.get("store_id", "unknown"),
        "correlation_id": event["correlation_id"],
        "ingested_at": _utc_now_iso(),
        **payload,
    }

    if event["event_type"] == "inventory_snapshot":
        dos = days_of_stock(
            current_stock=float(payload.get("current_stock", 0)),
            avg_daily_sales=float(payload.get("avg_daily_sales", 0)),
        )
        if dos is not None:
            item["days_of_stock"] = dos

    return item
