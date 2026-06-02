# 0003 — Resiliencia del pipeline: DLQ + fallos parciales de batch

- **Estado**: Aceptada
- **Fecha**: 2026-05-29

## Contexto

El pipeline procesa eventos en batches (SQS → processor, DynamoDB Streams →
analyzer). Un batch puede tener 10 mensajes y fallar solo uno. El comportamiento
por defecto de Lambda es marcar **todo el batch** como fallido y reintentarlo,
lo que reprocesa los 9 mensajes que sí pasaron — duplicando trabajo y, peor, en
el analyzer, duplicando llamadas costosas a Bedrock.

Además, hay dos tipos de fallo distintos que no deben tratarse igual:

- **Evento malformado** (no cumple el contrato): reintentarlo nunca va a
  funcionar; solo satura la cola.
- **Fallo transitorio** (throttling de DynamoDB, timeout): reintentar tiene
  sentido.

## Decisión

1. **Reporte de fallos parciales** (`ReportBatchItemFailures`): los handlers
   devuelven solo los `itemIdentifier` que fallaron. SQS/Streams reintenta
   únicamente esos, no el batch completo.
2. **DLQ con `maxReceiveCount = 3`**: tras 3 reintentos fallidos, el mensaje va a
   la Dead Letter Queue (retención 14 días) en lugar de perderse en silencio.
3. **Distinción de errores en el handler**:
   - Evento malformado → se loguea como `invalid_event` y se **descarta** (no
     entra a `batchItemFailures`).
   - Fallo transitorio → se reporta y se reintenta.
4. **Idempotencia**: el `event_id` (`{timestamp}#{correlation_id}`) hace que
   reprocesar el mismo evento sobrescriba el item en vez de duplicarlo.
5. **dlq_monitor**: una Lambda revisa la DLQ cada 6h y alerta vía SNS si hay
   mensajes, para que un fallo persistente no quede invisible.

## Consecuencias

**Positivas**
- No se reprocesan mensajes buenos; no se gastan créditos de Bedrock de más.
- Ningún evento se pierde en silencio: o se procesa, o queda en la DLQ con alerta.
- Errores no recuperables no saturan la cola de reintentos.

**Negativas**
- El handler debe clasificar el tipo de error explícitamente (más código), pero
  es la única forma de no reintentar lo irreintetable.
