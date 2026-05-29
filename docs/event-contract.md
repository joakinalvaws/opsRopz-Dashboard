# Contrato de eventos retail

Schema compartido entre el **simulador** (productor, en el VPS) y la **Lambda
processor** (consumidor, en AWS). Los eventos viajan por SQS como JSON.

## Envelope

Todos los eventos comparten esta estructura:

```json
{
  "correlation_id": "a3f9c2d1-...",
  "event_type": "inventory_snapshot",
  "timestamp": "2026-05-29T14:30:00Z",
  "store_id": "lima-centro",
  "sku": "LECHE_GLORIA_1L",
  "payload": { }
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `correlation_id` | string (UUID) | Identificador único para trazabilidad end-to-end. Lo genera el simulador y viaja por todo el pipeline. |
| `event_type` | string (enum) | Tipo de evento. Determina la forma de `payload`. |
| `timestamp` | string (ISO 8601 UTC) | Momento en que ocurrió el evento. |
| `store_id` | string | Identificador de la tienda. |
| `sku` | string | SKU del producto (clave de partición en DynamoDB). |
| `payload` | object | Datos específicos del tipo de evento. |

## Tipos de evento y payload

### `inventory_snapshot`
Foto del stock actual de un SKU. El processor calcula `days_of_stock`.

```json
{
  "current_stock": 72,
  "avg_daily_sales": 48.0
}
```

### `sale`
Una venta registrada.

```json
{
  "units": 3,
  "unit_price": 4.50,
  "total": 13.50
}
```

### `supplier_order`
Estado de un pedido a proveedor.

```json
{
  "order_id": "2241",
  "supplier": "Alicorp",
  "promised_date": "2026-05-26",
  "status": "in_transit"
}
```

## Item resultante en DynamoDB

La Lambda processor normaliza el evento y guarda un item con clave compuesta
(`sku` = hash, `event_id` = range), añadiendo los KPIs derivados:

```json
{
  "sku": "LECHE_GLORIA_1L",
  "event_id": "2026-05-29T14:30:00Z#a3f9c2d1-...",
  "timestamp": "2026-05-29T14:30:00Z",
  "event_type": "inventory_snapshot",
  "store_id": "lima-centro",
  "correlation_id": "a3f9c2d1-...",
  "current_stock": 72,
  "avg_daily_sales": 48.0,
  "days_of_stock": 1.5,
  "ingested_at": "2026-05-29T14:30:02Z"
}
```

### Sort key `event_id`

El sort key es `"{timestamp}#{correlation_id}"`, no el timestamp pelado.
Razón: dos eventos del mismo SKU en el mismo instante (p. ej. una venta y un
snapshot de inventario) compartirían la clave `(sku, timestamp)` y uno
sobrescribiría al otro — pérdida silenciosa de datos. El prefijo de timestamp
mantiene el orden cronológico para queries por rango de tiempo; el sufijo de
`correlation_id` garantiza unicidad. El atributo `timestamp` se conserva
aparte para queries y legibilidad.

## Garantías

- **Idempotencia**: reprocesar el mismo evento produce el mismo `event_id`
  (mismo timestamp + mismo correlation_id), así que sobrescribe el item en
  lugar de duplicarlo.
- **Sin colisiones**: eventos distintos del mismo SKU en el mismo instante
  tienen `correlation_id` distinto → `event_id` distinto → no se pisan.
- **Trazabilidad**: el `correlation_id` aparece en todos los logs estructurados
  desde el simulador hasta la notificación.
