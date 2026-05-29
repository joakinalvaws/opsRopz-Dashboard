# 0001 — Arquitectura híbrida AWS + VPS

- **Estado**: Aceptada
- **Fecha**: 2026-05-28

## Contexto

OpsRopz debe operar 24/7 dentro de la capa gratuita de AWS, pero algunos
componentes no encajan bien en un modelo serverless puro o gratuito:

- El **simulador de eventos** necesita correr cada 5 minutos de forma continua.
  Hacerlo con EventBridge + Lambda es posible, pero un cron en un VPS que ya
  existe es más simple y no consume invocaciones.
- **n8n** y **Evolution API** (WhatsApp) son servicios de larga ejecución con
  estado, inadecuados para Lambda.
- Se necesita un **fallback de LLM** cuando se agoten los créditos de Bedrock,
  que pueda llamar a una API externa sin depender de la cuenta AWS.

## Decisión

Adoptar una arquitectura híbrida:

- **AWS (serverless, event-driven)**: Lambda, SQS+DLQ, DynamoDB, SNS,
  EventBridge, API Gateway, Bedrock, S3, SES, CloudWatch. Núcleo del sistema.
- **VPS Hostinger (servicios 24/7 con estado)**: simulador Python (cron), n8n,
  Evolution API y el fallback LLM.

El acoplamiento entre capas es por **SNS → webhook HTTPS** (AWS → n8n) y por
**SQS** (simulador → AWS), manteniendo ambos lados desacoplados.

## Consecuencias

**Positivas**
- Costo cercano a cero: el VPS ya está pagado, AWS se mantiene en capa gratuita.
- Cada componente vive donde mejor encaja (stateless en Lambda, stateful en VPS).
- El fallback LLM no depende de AWS, así que sobrevive a créditos agotados.

**Negativas / riesgos**
- El webhook SNS → n8n exige que el VPS tenga **dominio + SSL** públicos para
  confirmar la suscripción al topic. Debe estar listo antes de Semana 3.
- Dos planos operativos (AWS + VPS) que monitorear. Se mitiga con
  correlation IDs end-to-end y logging estructurado en ambos lados.

## Alternativas descartadas

- **Todo en AWS**: EventBridge para el simulador y un servicio de mensajería
  gestionado. Más caro y con menos control sobre WhatsApp.
- **Todo en VPS**: perdería la experiencia con AWS serverless, que es el
  objetivo de aprendizaje y portafolio del proyecto.
