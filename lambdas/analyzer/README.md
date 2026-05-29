# Lambda `analyzer`

Disparada por **DynamoDB Streams** de la tabla `operations`. Por cada nuevo item
KPI evalúa reglas de anomalía; si detecta una, pide a **Bedrock (Claude Haiku 4.5)**
un análisis en lenguaje natural con recomendación y emite una alerta estructurada.

## Responsabilidad

- **Trigger**: DynamoDB Streams (NEW_IMAGE) con reporte de fallos parciales (por `SequenceNumber`).
- **Detección**: `anomalies.evaluate()` aplica umbrales del plan (stock < 3 días → crítico, etc.).
- **Análisis IA**: solo se llama a Bedrock cuando hay anomalía (controla costos).
- **Salida**: log estructurado `alert_generated` con severidad, análisis y `prompt_version`.
  La publicación a SNS se cablea en Semana 3.
- **Degradación elegante**: si Bedrock falla, loguea `analysis_failed` y continúa
  (no reintenta vía stream para evitar loops costosos; el fallback LLM en VPS cubre Semana 3).

## Archivos

| Archivo | Rol |
|---|---|
| `handler.py` | Entry point del stream; orquesta detección + análisis. |
| `anomalies.py` | Reglas puras de detección de anomalías y severidad. |
| `prompts.py` | Prompt versionado (`PROMPT_VERSION`) + cuerpo Messages API. |
| `bedrock_client.py` | invoke_model con retries de backoff exponencial (1s, 2s, 4s). |
| `logging_utils.py` | Logging estructurado JSON. |

## Variables de entorno

| Variable | Descripción | Default |
|---|---|---|
| `BEDROCK_MODEL_ID` | Inference profile de Bedrock (Haiku 4.5 exige profile, no model ID directo) | `us.anthropic.claude-haiku-4-5-20251001-v1:0` |

## Tests

```bash
pytest lambdas/analyzer --cov=lambdas/analyzer
```

Bedrock se mockea con un cliente falso inyectable — no requiere AWS ni consume créditos.
