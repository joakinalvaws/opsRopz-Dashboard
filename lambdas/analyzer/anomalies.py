"""Detección de anomalías sobre items KPI.

Funciones puras (sin AWS ni I/O) que evalúan un item ya normalizado por el
processor y devuelven una Anomaly si cruza algún umbral. Los umbrales salen de
las tablas de módulos retail del plan (secciones 4.1-4.4).
"""

from __future__ import annotations

from dataclasses import dataclass

# Niveles de severidad — ordenados de mayor a menor.
CRITICAL = "critico"
ALERT = "alerta"
INFO = "info"

# Umbrales (del plan).
DAYS_OF_STOCK_CRITICAL = 3.0  # < 3 días de stock → crítico
SALES_DROP_ALERT = -30.0  # ventas vs promedio < -30% → crítico/alerta


@dataclass(frozen=True)
class Anomaly:
    rule: str
    severity: str
    detail: str


def evaluate(item: dict) -> Anomaly | None:
    """Devuelve la Anomaly de mayor severidad para el item, o None si está sano."""
    event_type = item.get("event_type")

    if event_type == "inventory_snapshot":
        return _evaluate_inventory(item)
    if event_type == "sale":
        return _evaluate_sale(item)
    return None


def _to_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _evaluate_inventory(item: dict) -> Anomaly | None:
    dos = _to_float(item.get("days_of_stock"))
    if dos is None:
        return None
    if dos < DAYS_OF_STOCK_CRITICAL:
        return Anomaly(
            rule="stock_critico",
            severity=CRITICAL,
            detail=f"Stock para {dos} días (umbral < {DAYS_OF_STOCK_CRITICAL}).",
        )
    return None


def _evaluate_sale(item: dict) -> Anomaly | None:
    # Requiere que el item traiga la desviación vs promedio (la calcula el
    # processor cuando hay histórico). Si no está, no se puede evaluar aún.
    deviation = _to_float(item.get("sales_vs_average_pct"))
    if deviation is None:
        return None
    if deviation <= SALES_DROP_ALERT:
        return Anomaly(
            rule="caida_ventas",
            severity=CRITICAL if deviation <= 2 * SALES_DROP_ALERT else ALERT,
            detail=f"Ventas {deviation}% vs promedio (umbral <= {SALES_DROP_ALERT}%).",
        )
    return None
