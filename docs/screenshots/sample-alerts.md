# Ejemplos de alertas generadas por IA

Salida **real** de la Lambda `analyzer` invocando **Amazon Bedrock (Claude Haiku 4.5)**
en producción. Cada alerta nace de un evento de inventario que atraviesa el pipeline
event-driven completo:

```
evento → SQS → Lambda processor → DynamoDB → DynamoDB Streams → Lambda analyzer → Bedrock → alerta
```

El `analyzer` solo invoca a Bedrock cuando una regla de anomalía se dispara (aquí,
`stock_critico`: días de stock restantes < 3). El prompt está versionado (`v1`).

---

### 🚨 LECHE_GLORIA_1L — lima-centro

| Stock actual | Ventas/día | Días de stock | Severidad | Regla |
|---|---|---|---|---|
| 24 | 48 | **0.5** | `crítico` | `stock_critico` |

> El producto LECHE_GLORIA_1L en la tienda lima-centro se agotará en medio día porque
> las ventas diarias (48 unidades) duplican el stock disponible (24 unidades), lo que
> indica una demanda muy superior a la oferta actual. Te recomiendo aumentar
> inmediatamente la orden de compra a este proveedor para un reabastecimiento de
> emergencia en las próximas 24 horas, considerando que es un producto de alto
> movimiento en zona céntrica.

---

### 🚨 ARROZ_COSTENO_5KG — lima-norte

| Stock actual | Ventas/día | Días de stock | Severidad | Regla |
|---|---|---|---|---|
| 40 | 22 | **1.82** | `crítico` | `stock_critico` |

> El arroz Costeño de 5kg en Lima Norte se agotará en menos de 2 días si mantiene el
> ritmo de ventas actual de 22 unidades diarias, lo que representa un riesgo crítico de
> desabastecimiento en un producto de alto movimiento. Recomiendo realizar una orden de
> reposición inmediata de al menos 150 unidades (aproximadamente 7 días de stock) a tu
> proveedor hoy mismo para evitar quiebres de inventario y pérdida de ventas en los
> próximos días.

---

### 🚨 ACEITE_PRIMOR_1L — arequipa-01

| Stock actual | Ventas/día | Días de stock | Severidad | Regla |
|---|---|---|---|---|
| 20 | 15 | **1.33** | `crítico` | `stock_critico` |

> El producto ACEITE_PRIMOR_1L en la tienda arequipa-01 se agotará en menos de 2 días si
> continúa el ritmo de ventas actual, lo que representa un riesgo alto de
> desabastecimiento. Te recomiendo realizar una reposición urgente de al menos 45
> unidades (equivalente a 3 días de venta promedio) en las próximas 24 horas para evitar
> pérdidas de ventas y garantizar la disponibilidad del producto.

---

### 🚨 ATUN_FLORIDA_170G — lima-centro

| Stock actual | Ventas/día | Días de stock | Severidad | Regla |
|---|---|---|---|---|
| 60 | 40 | **1.5** | `crítico` | `stock_critico` |

> El stock de atún Florida 170g en lima-centro se agotará en 1.5 días con las ventas
> actuales, por debajo del mínimo operativo de 3 días que requiere esta tienda.
> Recomiendo que el gerente coordine con el proveedor para realizar una compra de
> urgencia de al menos 80 unidades esta semana, asegurando cobertura de 2 días
> adicionales mientras se normaliza el ciclo de reorden regular.

---

> Generado el 2026-05-29 con `anthropic.claude-haiku-4-5-20251001-v1:0`
> (inference profile `us.*`) en `us-east-1`. Cada alerta incluye un `correlation_id`
> que permite rastrear el evento de extremo a extremo en CloudWatch Logs Insights.
