# Lambda `query`

Expone KPIs de inventario y el historial de alertas al dashboard, vía API Gateway
(REST) con API key + rate limiting. Solo lectura sobre DynamoDB.

## Responsabilidad

- **Trigger**: API Gateway (integración Lambda proxy).
- **Rutas**:
  - `GET /kpis` → último snapshot de inventario por SKU, conteo de ventas, stock crítico.
  - `GET /alerts` → últimas 50 alertas (tabla `alerts`, orden temporal descendente).
- **Salida**: JSON con `Access-Control-Allow-Origin: *`. Los `Decimal` de DynamoDB se
  convierten a number.
- **Errores**: ruta desconocida → 404; fallo interno → 500 logueado como `query_failed`.

## Archivos

| Archivo | Rol |
|---|---|
| `handler.py` | Routing por path, lectura de KPIs y alertas, serialización JSON. |
| `logging_utils.py` | Logging estructurado JSON. |

## Variables de entorno

| Variable | Descripción |
|---|---|
| `OPERATIONS_TABLE` | Tabla de operaciones (scan para KPIs) |
| `ALERTS_TABLE` | Tabla de alertas (query del historial) |

## Tests

```bash
pytest lambdas/query
```

Los tests mockean DynamoDB con tablas fake — no requieren AWS real.
