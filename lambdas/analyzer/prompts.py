"""Prompts versionados para el análisis IA.

Versionar el prompt permite testear su formato con casos conocidos y rastrear
qué versión generó cada análisis.
"""

from __future__ import annotations

PROMPT_VERSION = "v1"

SYSTEM_PROMPT = (
    "Eres un analista de operaciones de retail en Perú. Recibes una anomalía "
    "detectada automáticamente en una tienda y debes explicarla de forma clara "
    "para el gerente, con UNA recomendación accionable y concreta. "
    "Responde en español, en 2 a 3 oraciones, sin markdown ni listas."
)


def build_user_prompt(item: dict, anomaly_detail: str) -> str:
    """Arma el mensaje de usuario con el contexto real del KPI."""
    sku = item.get("sku", "desconocido")
    store = item.get("store_id", "desconocida")
    lines = [
        f"Anomalía: {anomaly_detail}",
        f"Producto (SKU): {sku}",
        f"Tienda: {store}",
    ]
    for label, key in (
        ("Stock actual", "current_stock"),
        ("Ventas promedio diarias", "avg_daily_sales"),
        ("Días de stock restantes", "days_of_stock"),
    ):
        if item.get(key) is not None:
            lines.append(f"{label}: {item[key]}")
    return "\n".join(lines)


def build_bedrock_body(item: dict, anomaly_detail: str, max_tokens: int = 400) -> dict:
    """Cuerpo de invoke_model para Claude en Bedrock (Messages API)."""
    return {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "system": SYSTEM_PROMPT,
        "messages": [
            {"role": "user", "content": build_user_prompt(item, anomaly_detail)},
        ],
    }
