"""Generación de eventos retail realistas.

Lógica pura (sin red ni AWS) para que sea testeable de forma determinista
pasando una instancia de random.Random con semilla.
"""

from __future__ import annotations

import random
import uuid
from datetime import UTC, datetime
from typing import Any

STORES = ["lima-centro", "lima-norte", "arequipa-01"]

# Catálogo de productos con su perfil de ventas promedio (und/día).
CATALOG = [
    ("LECHE_GLORIA_1L", 48.0),
    ("ARROZ_COSTENO_5KG", 22.0),
    ("ACEITE_PRIMOR_1L", 15.0),
    ("FIDEOS_DON_VITTORIO", 30.0),
    ("ATUN_FLORIDA_170G", 40.0),
    ("DETERGENTE_BOLIVAR_2KG", 12.0),
]

SUPPLIERS = ["Alicorp", "Gloria", "Nestlé", "P&G"]
ORDER_STATUSES = ["pending", "confirmed", "in_transit"]


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _envelope(event_type: str, sku: str, rng: random.Random, payload: dict[str, Any]) -> dict:
    return {
        "correlation_id": str(uuid.UUID(int=rng.getrandbits(128))),
        "event_type": event_type,
        "timestamp": _now_iso(),
        "store_id": rng.choice(STORES),
        "sku": sku,
        "payload": payload,
    }


def make_inventory_snapshot(rng: random.Random) -> dict:
    sku, avg_sales = rng.choice(CATALOG)
    # A veces genera stock crítico (< 3 días) para ejercitar el analyzer.
    days = rng.choice([0.8, 1.5, 2.0, 5.0, 10.0, 25.0])
    current_stock = round(avg_sales * days)
    return _envelope(
        "inventory_snapshot",
        sku,
        rng,
        {"current_stock": current_stock, "avg_daily_sales": avg_sales},
    )


def make_sale(rng: random.Random) -> dict:
    sku, _ = rng.choice(CATALOG)
    units = rng.randint(1, 8)
    unit_price = round(rng.uniform(2.5, 25.0), 2)
    return _envelope(
        "sale",
        sku,
        rng,
        {"units": units, "unit_price": unit_price, "total": round(units * unit_price, 2)},
    )


def make_supplier_order(rng: random.Random) -> dict:
    sku, _ = rng.choice(CATALOG)
    return _envelope(
        "supplier_order",
        sku,
        rng,
        {
            "order_id": str(rng.randint(2000, 2999)),
            "supplier": rng.choice(SUPPLIERS),
            "promised_date": _now_iso()[:10],
            "status": rng.choice(ORDER_STATUSES),
        },
    )


_GENERATORS = (make_inventory_snapshot, make_sale, make_supplier_order)


def generate_batch(count: int, rng: random.Random | None = None) -> list[dict]:
    """Genera `count` eventos de tipos variados."""
    rng = rng or random.Random()
    return [rng.choice(_GENERATORS)(rng) for _ in range(count)]
