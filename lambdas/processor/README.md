# Lambda `processor`

Consume eventos retail de la cola SQS `events`, los normaliza, calcula KPIs y
los persiste en la tabla DynamoDB `operations`.

## Responsabilidad

- **Trigger**: SQS (event source mapping) con reporte de fallos parciales.
- **Entrada**: batch de mensajes SQS; cada body es un evento del
  [contrato de eventos](../../docs/event-contract.md).
- **Salida**: items en DynamoDB con clave `(sku, timestamp)` + KPIs derivados.
- **Errores**:
  - Evento malformado → se loguea como `invalid_event` y se descarta (no
    reintenta, no satura la DLQ).
  - Fallo transitorio (p. ej. throttling de DynamoDB) → se reporta en
    `batchItemFailures`; SQS reintenta hasta 3 veces y luego va a la DLQ.

## Archivos

| Archivo | Rol |
|---|---|
| `handler.py` | Entry point Lambda, orquesta el batch y maneja errores. |
| `normalize.py` | `build_item()` — valida envelope y arma el item (pura). |
| `kpis.py` | Funciones puras de KPIs (`days_of_stock`, etc.). |
| `logging_utils.py` | Logging estructurado JSON con `correlation_id`. |

## Variables de entorno

| Variable | Descripción | Default |
|---|---|---|
| `OPERATIONS_TABLE` | Nombre de la tabla DynamoDB | `opsropz-operations-dev` |

## Tests

```bash
pytest lambdas/processor --cov=lambdas/processor
```

Los tests del handler usan `moto` para mockear DynamoDB — no requieren AWS real.
