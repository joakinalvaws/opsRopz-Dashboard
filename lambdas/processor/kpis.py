"""Funciones puras de cálculo de KPIs.

Sin dependencias de AWS ni de I/O para que sean triviales de testear y de
reutilizar desde el analyzer.
"""

from __future__ import annotations


def days_of_stock(current_stock: float, avg_daily_sales: float) -> float | None:
    """Días de stock restantes al ritmo de ventas actual.

    Devuelve None si no hay ventas (no se puede proyectar agotamiento) o si los
    datos son inválidos.
    """
    if avg_daily_sales <= 0:
        return None
    if current_stock < 0:
        return None
    return round(current_stock / avg_daily_sales, 2)


def stock_drop_pct(previous_stock: float, current_stock: float) -> float | None:
    """Caída porcentual de stock entre dos snapshots (0-100).

    Un valor positivo indica reducción. Devuelve None si no hay base previa.
    """
    if previous_stock <= 0:
        return None
    drop = (previous_stock - current_stock) / previous_stock * 100
    return round(drop, 2)


def sales_vs_average_pct(today_sales: float, avg_sales: float) -> float | None:
    """Desviación porcentual de las ventas de hoy vs el promedio histórico.

    Negativo = por debajo del promedio. Devuelve None sin base de comparación.
    """
    if avg_sales <= 0:
        return None
    return round((today_sales - avg_sales) / avg_sales * 100, 2)
