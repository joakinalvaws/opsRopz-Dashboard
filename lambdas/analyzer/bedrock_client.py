"""Cliente de Amazon Bedrock con retries de backoff exponencial.

Aísla la invocación de Claude Haiku 4.5 para que el handler no maneje detalles
de throttling ni parsing de la respuesta.
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable

import boto3
from botocore.exceptions import ClientError

# Inference profile (no el model ID directo): Claude Haiku 4.5 no admite on-demand
# por model ID, exige invocar vía profile.
MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")

# Errores transitorios de Bedrock que justifican reintento.
_RETRYABLE = {
    "ThrottlingException",
    "ModelTimeoutException",
    "ServiceUnavailableException",
    "InternalServerException",
}

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = boto3.client("bedrock-runtime")
    return _client


class BedrockError(RuntimeError):
    """Fallo no recuperable al invocar Bedrock."""


def invoke(
    body: dict,
    *,
    max_attempts: int = 3,
    sleep: Callable[[float], None] = time.sleep,
    client=None,
) -> str:
    """Invoca el modelo y devuelve el texto generado.

    Reintenta con backoff exponencial (1s, 2s, 4s) ante errores transitorios.
    `sleep` y `client` son inyectables para tests.
    """
    client = client or _get_client()
    payload = json.dumps(body)

    last_error: Exception | None = None
    for attempt in range(max_attempts):
        try:
            response = client.invoke_model(
                modelId=MODEL_ID,
                body=payload,
                contentType="application/json",
                accept="application/json",
            )
            return _extract_text(response)
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")
            last_error = exc
            if code not in _RETRYABLE or attempt == max_attempts - 1:
                raise BedrockError(f"Bedrock falló ({code}): {exc}") from exc
            sleep(2**attempt)  # 1s, 2s, 4s

    raise BedrockError(f"Bedrock agotó reintentos: {last_error}")


def _extract_text(response: dict) -> str:
    raw = response["body"].read()
    data = json.loads(raw)
    parts = data.get("content", [])
    return "".join(p.get("text", "") for p in parts if p.get("type") == "text").strip()
