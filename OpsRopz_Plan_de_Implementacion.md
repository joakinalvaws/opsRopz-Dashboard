# OpsRopz — Plan de Implementación

> Sistema de inteligencia operacional para retail, construido con AWS serverless e IA generativa.

> **Recursos AWS confirmados**: S3 `opsropz-tfstate` · DynamoDB `opsropz-tflocks` · IAM `opsropz-dev` · Bedrock `anthropic.claude-haiku-4-5-20251001-v1:0` · Región `us-east-1`
> Diseñado para operar dentro de la capa gratuita de AWS, con arquitectura híbrida sobre VPS Hostinger.

---

## Índice

1. [Resumen ejecutivo](#1-resumen-ejecutivo)
2. [El problema que resuelve](#2-el-problema-que-resuelve)
3. [Cómo funciona — flujo end-to-end](#3-cómo-funciona--flujo-end-to-end)
4. [Operaciones monitoreadas](#4-qué-operaciones-monitorea--módulos-retail)
5. [Canales de notificación](#5-canales-de-notificación)
6. [Arquitectura híbrida](#6-arquitectura-híbrida--aws--vps)
7. [Observabilidad y resiliencia](#7-observabilidad-y-resiliencia)
8. [Estrategia de testing](#8-estrategia-de-testing)
9. [Buenas prácticas aplicadas](#9-buenas-prácticas-aplicadas)
10. [Stack tecnológico](#10-stack-tecnológico-completo)
11. [Plan semana a semana](#11-plan-de-construcción--semana-a-semana)
12. [Estructura del repositorio](#12-estructura-del-repositorio)
13. [Cómo describirlo en el CV](#13-cómo-describirlo-en-el-cv)

---

## 1. Resumen ejecutivo

**OpsRopz** es un sistema que monitorea las operaciones de una tienda retail en tiempo real, detecta problemas automáticamente con IA generativa y notifica al equipo encargado por WhatsApp, Slack y email — sin que nadie tenga que revisar planillas o dashboards manualmente.

El sistema invierte la dinámica tradicional: en lugar de que los gerentes revisen reportes constantemente, **el sistema los busca a ellos cuando algo necesita atención**, explicándolo en lenguaje natural con recomendaciones accionables.

**Modelo operativo**: diseñado para operar dentro de la capa gratuita de AWS, con servicios siempre-gratuitos como base (Lambda, DynamoDB, SQS) y créditos iniciales para Bedrock durante los primeros meses.

---

## 2. El problema que resuelve

En empresas retail medianas, los encargados de operaciones se enteran tarde de los problemas:

- Un producto se agota antes de que alguien notara el ritmo de ventas
- Un pedido a proveedor lleva días retrasado sin seguimiento
- Las ventas del día caen 30% y nadie se entera hasta el cierre
- Los reportes en Excel los lee nadie hasta el cierre de mes

OpsRopz resuelve esto con un sistema que **vigila 24/7, piensa antes de alertar, y notifica con contexto**.

---

## 3. Cómo funciona — flujo end-to-end

```
Eventos retail (VPS) → SQS → Lambda (procesador) → DynamoDB (KPIs)
                       ↓DLQ              ↓
                                Lambda (analizador IA) → Bedrock/Claude
                                          ↓
                                        SNS → CloudWatch
                                          ↓
                          n8n (VPS) → WhatsApp / Slack
                          SES → Email (reporte diario)
                                          ↓
                      API Gateway → Dashboard Next.js (Vercel)
                          (con auth + rate limiting)
```

**Paso 1 — Ingesta**: Un simulador en Python (corriendo en el VPS) genera eventos retail realistas cada 5 minutos y los envía a una cola SQS en AWS. Cada evento lleva un `correlation_id` único para trazabilidad. En una empresa real, aquí se conectaría el ERP o POS.

**Paso 2 — Procesamiento**: Una Lambda se dispara con cada mensaje, normaliza los datos, calcula KPIs (días de stock restante, tasa de retraso, eficiencia) y los guarda en DynamoDB. Los mensajes que fallan tras 3 reintentos van a una Dead Letter Queue (DLQ) para análisis posterior.

**Paso 3 — Análisis IA**: Cuando se detecta una anomalía según umbrales definidos, otra Lambda consulta a Amazon Bedrock (Claude Haiku 4.5) con el contexto real y obtiene un análisis en lenguaje natural con recomendaciones.

**Paso 4 — Notificación**: SNS dispara la alerta → n8n (en el VPS) la recibe y la envía por WhatsApp y/o Slack según severidad. EventBridge programa además un reporte PDF diario que se envía por email. Cada notificación incluye el `correlation_id` para debugging.

**Paso 5 — Visibilidad**: Un dashboard en Next.js desplegado en Vercel consulta API Gateway → Lambda → DynamoDB. Muestra KPIs en vivo, historial de alertas y un chat de consulta en lenguaje natural. Protegido con autenticación y rate limiting.

---

## 4. Qué operaciones monitorea — módulos retail

### 4.1 Inventario y stock

| Métrica | Umbral | Severidad |
|---|---|---|
| Stock restante según ventas actuales | < 3 días | Crítico |
| Producto sin movimiento de ventas | > 7 días | Alerta |
| Caída brusca de stock en un día | > 40% | Alerta |
| Sobrestock acumulado sin rotación | > 90 días | Info |

### 4.2 Ventas y rendimiento

| Métrica | Umbral | Severidad |
|---|---|---|
| Ventas del día vs promedio histórico | < -30% | Crítico |
| Pico de ventas inusual | > 3x promedio | Alerta |
| Caída del ticket promedio vs misma franja | < -20% | Alerta |
| Resumen de ventas por franja horaria | — | Info |

### 4.3 Pedidos a proveedores

| Métrica | Umbral | Severidad |
|---|---|---|
| Pedido retrasado sobre fecha prometida | > 2 días | Crítico |
| Proveedor con múltiples pedidos retrasados | > 2 en un mes | Alerta |
| Pedido pendiente de confirmar | > 24 horas | Info |

### 4.4 Operaciones de tienda

| Métrica | Umbral | Severidad |
|---|---|---|
| Caída en ratio de conversión | < -25% vs día anterior | Alerta |
| Producto con calificación baja sostenida | < 3.0 en 7 días | Alerta |
| Reporte diario consolidado | — | Info |

---

## 5. Canales de notificación

### WhatsApp (Evolution API en VPS)
Para alertas **críticas** que requieren acción inmediata. Mensaje directo al gerente o dueño.

> 🚨 *Stock crítico* — Leche Gloria 1L tiene stock para **1.5 días**.
> Ventas promedio: 48 und/día. Stock actual: 72 und.
> Recomiendo reordenar 300 und hoy.
> *Ref: a3f9c2*

### Slack (vía n8n)
Para **alertas del equipo** de operaciones. Colaborativo, con contexto, sin interrumpir.

> 📦 **#ops-alertas** — Pedido #2241 (Proveedor Alicorp) lleva **3 días de retraso**.
> Impacto estimado: 4 SKUs quedan sin stock en 48h. Contactar proveedor.

### Email (AWS SES)
Reporte PDF diario automático a las 8am. Resumen ejecutivo con KPIs, alertas del día anterior y proyecciones de stock.

### Lógica de routing por severidad

| Nivel | Va a | Ejemplo |
|---|---|---|
| Crítico | WhatsApp + Slack #ops-alertas | Stock < 3 días |
| Alerta | Solo Slack #ops-alertas | Ventas -30% |
| Info | Reporte diario por email | Resumen del día |

**Idempotencia**: cada notificación incluye un `notification_id` único. Si el mismo evento dispara la alerta dos veces (reintentos, fallos parciales), n8n detecta el ID duplicado y no reenvía.

---

## 6. Arquitectura híbrida — AWS + VPS

### Capa AWS (Always Free — siempre gratuita)

| Servicio | Función | Capa gratuita |
|---|---|---|
| Lambda | Procesa eventos, calcula KPIs, orquesta lógica | 1M req/mes siempre |
| DynamoDB | Almacena métricas, KPIs e historial | 25 GB siempre |
| SQS + DLQ | Cola de eventos con Dead Letter Queue | 1M req/mes siempre |
| API Gateway | Capa de acceso para el dashboard | 1M llamadas año 1 |
| SNS + CloudWatch | Disparo de alertas y observabilidad | Generosa siempre |
| S3 | Almacenamiento de reportes PDF | 5 GB siempre |
| Bedrock (Claude Haiku 4.5) | Análisis IA — consume créditos | $200 créditos iniciales |
| Secrets Manager | Almacenamiento seguro de API keys | Trial 30 días |

### Capa VPS Hostinger (servicios 24/7)

| Servicio | Función |
|---|---|
| Simulador Python | Genera eventos retail cada 5 min via cron |
| n8n | Orquesta alertas SNS → WhatsApp/Slack |
| Evolution API | Capa de mensajería WhatsApp |
| Fallback LLM | Cuando se agoten créditos Bedrock |

### Estrategia de capa gratuita

1. **Reclamar los $200 en créditos AWS** completando las 5 tareas de onboarding al crear la cuenta (una de ellas es probar Bedrock — ya cuenta para el proyecto).
2. **Usar Bedrock durante los primeros 6 meses** mientras hay créditos disponibles.
3. **Configurar AWS Budgets con alerta a $1** para evitar sorpresas.
4. **Tagging consistente** en todos los recursos (`Project=OpsRopz`, `Environment=prod`, `ManagedBy=Terraform`) para tracking de costos en Cost Explorer.
5. **A partir del mes 7**: si se agotaron créditos, el fallback llama a OpenAI/Claude API directamente desde el VPS.

---

## 7. Observabilidad y resiliencia

Sistema diseñado para fallar elegantemente y dejar trazabilidad completa.

### Logging estructurado
Todos los logs en formato JSON con campos consistentes: `timestamp`, `correlation_id`, `service`, `level`, `event_type`, `message`. Esto permite consultas eficientes en CloudWatch Insights.

```python
# Ejemplo de log estructurado
logger.info(json.dumps({
    "correlation_id": event["correlation_id"],
    "service": "processor",
    "event_type": "kpi_calculated",
    "sku": "LECHE_GLORIA_1L",
    "days_of_stock": 1.5
}))
```

### Correlation IDs end-to-end
Cada evento se etiqueta con un `correlation_id` único en el simulador. Ese ID viaja con el evento a través de SQS → Lambda → DynamoDB → SNS → n8n → WhatsApp. Si algo falla, se puede rastrear el evento completo con una sola búsqueda.

### Dead Letter Queue (DLQ)
SQS configurado con DLQ después de 3 reintentos fallidos. Una Lambda revisa la DLQ diariamente y envía alerta si tiene mensajes. Esto evita pérdida silenciosa de eventos.

### Retries con backoff exponencial
Las llamadas a Bedrock implementan retry con backoff exponencial (1s, 2s, 4s) para manejar throttling temporal sin colapsar el sistema.

### CloudWatch Dashboard
Un dashboard consolidado muestra:
- Eventos procesados por minuto
- Latencia de cada Lambda (p50, p95, p99)
- Errores por servicio
- Alertas disparadas por severidad
- Costo acumulado del mes
- Mensajes en DLQ

### Alertas de salud del sistema
CloudWatch Alarms configuradas para:
- Errores en Lambdas > 5% en 5 minutos
- Mensajes en DLQ > 0
- Latencia de Lambda > 3 segundos
- Costo proyectado del mes > $5

---

## 8. Estrategia de testing

### Tests unitarios (pytest)
Cada Lambda tiene tests unitarios para su lógica core:
- `processor`: cálculo de KPIs, normalización de datos
- `analyzer`: detección de anomalías, formato de prompt
- `query`: respuestas API correctas
- `daily_report`: generación de PDF

Cobertura objetivo: > 70% en la lógica de negocio.

### Tests de integración
- Test end-to-end: simulador → SQS → Lambda → DynamoDB (usando moto o LocalStack)
- Test de flujo de alerta: anomalía detectada → SNS → notificación
- Test del API: dashboard puede consultar KPIs correctamente

### Tests de prompts IA
Los prompts a Bedrock se versionan y testean con un set de casos conocidos para validar que las respuestas mantengan formato y calidad esperados.

### CI con GitHub Actions
Cada push a `main` ejecuta:
1. Lint (ruff, terraform fmt)
2. Tests unitarios
3. Tests de integración
4. Security scan de dependencias (pip-audit)
5. Build y deploy si todo pasa

---

## 9. Buenas prácticas aplicadas

### Seguridad
- **IAM con mínimo privilegio**: cada Lambda tiene un rol específico con solo los permisos que necesita (no roles compartidos).
- **Secrets Manager / SSM Parameter Store**: API keys de OpenAI, tokens de Slack y credenciales de Evolution API nunca en código ni en variables de entorno hardcoded.
- **API Gateway con autenticación**: API keys + rate limiting (100 req/min) para evitar abuso.
- **Cognito o Clerk** para auth del dashboard (a partir de Semana 5).
- **HTTPS obligatorio** en todos los endpoints.
- **Pre-commit hooks**: detectan secretos accidentalmente commiteados antes del push.

### Calidad de código
- **Pre-commit hooks**: `ruff` (lint), `black` (format), `terraform fmt`, `detect-secrets`.
- **Type hints** en todo el código Python.
- **Dependencias fijadas** (`requirements.txt` con versiones exactas, `pip-audit` en CI).
- **Separación de entornos**: namespacing por workspace en Terraform (`dev`, `prod`).
- **ADRs (Architecture Decision Records)** documentando decisiones técnicas en `/docs/decisions/`.

### Operación
- **Tagging consistente**: todos los recursos AWS llevan tags estándar para tracking de costos y ownership.
- **Idempotencia**: las Lambdas pueden recibir el mismo evento dos veces sin causar duplicados (verifican por `correlation_id`).
- **Graceful degradation**: si Bedrock falla, el sistema cae al fallback en VPS sin perder eventos.
- **Cost monitoring**: AWS Budgets + dashboard de costos consultado semanalmente.

### Documentación
- README profesional con diagrama de arquitectura, screenshots, demo en video.
- `/docs/decisions/` con ADRs numerados explicando el por qué de cada elección importante.
- Cada Lambda tiene su propio README con responsabilidad, inputs/outputs y ejemplos.
- Diagrama de arquitectura mantenido en draw.io o excalidraw (versionable como `.svg`).

---

## 10. Stack tecnológico completo

**AWS Core**: Lambda, SQS (+ DLQ), DynamoDB, SNS, EventBridge, API Gateway, Bedrock, S3, SES, CloudWatch, Secrets Manager, Cognito
**Backend y simulación**: Python 3.12, pytest, ruff, black
**Frontend**: Next.js 15, Recharts, Tailwind CSS
**Orquestación y mensajería**: n8n, Evolution API, Slack API
**Infraestructura como código**: Terraform + workspaces
**CI/CD**: GitHub Actions, pre-commit hooks
**Observabilidad**: CloudWatch Dashboards + Logs Insights, correlation IDs
**Testing**: pytest, moto (mocks AWS), pip-audit (security)
**Deploy**: Vercel (frontend), AWS (backend), VPS Hostinger (servicios 24/7)

---

## 11. Plan de construcción — semana a semana

### Semana 0 — Setup y fundamentos (2–3 días)

- [ ] Crear cuenta AWS en plan gratuito y reclamar los $200 en créditos
- [ ] Configurar AWS Budgets con alerta a $1 y $5
- [ ] Crear usuario IAM programático con políticas específicas (sin root)
- [ ] Crear repo en GitHub con estructura completa
- [ ] Definir tagging strategy (`Project=OpsRopz`, `Environment`, `Owner`)
- [ ] Instalar AWS CLI, Terraform, Python 3.12, Node 20
- [ ] Configurar pre-commit hooks (`ruff`, `black`, `terraform fmt`, `detect-secrets`)
- [ ] Crear workspace de Slack y obtener webhook del canal `#ops-alertas`
- [ ] Escribir primer ADR: "Por qué arquitectura híbrida AWS + VPS"

**Entregable**: cuenta lista, repo con CI inicial corriendo, presupuesto blindado, primer ADR.

---

### Semana 1 — Capa de datos serverless (5–7 días)

- [ ] Crear tabla DynamoDB `operations` con clave compuesta (sku, timestamp)
- [ ] Crear cola SQS `events-queue` + DLQ `events-dlq` con redrive policy (3 reintentos)
- [ ] Escribir Lambda `processor` en Python con logging estructurado JSON
- [ ] Implementar correlation IDs end-to-end (simulador → SQS → Lambda → DynamoDB)
- [ ] Escribir simulador en Python (VPS) que genera eventos retail realistas
- [ ] Configurar cron en VPS para enviar eventos a SQS cada 5 min
- [ ] Tests unitarios de `processor` con pytest (cobertura > 70%)
- [ ] Validar end-to-end: simulador → SQS → Lambda → DynamoDB
- [ ] **Capturar screenshots**: logs en CloudWatch, items en DynamoDB, mensaje en SQS
- [ ] Grabar primer mini-video (30 seg) del flujo funcionando

**Entregable**: pipeline event-driven funcionando con observabilidad y tests. Material visual para portafolio.

---

### Semana 2 — Capa de IA (5–7 días)

- [ ] Escribir Lambda `analyzer` que consulta KPIs recientes de DynamoDB
- [ ] Integrar Amazon Bedrock (Claude Haiku 4.5) con prompt versionado
- [ ] Implementar retries con backoff exponencial para llamadas a Bedrock
- [ ] Definir reglas de detección de anomalías (stock < 3 días, ventas < -30%, etc.)
- [ ] Implementar lógica de severidad (crítico / alerta / info)
- [ ] Mover API keys a AWS Secrets Manager (Bedrock, OpenAI fallback)
- [ ] Preparar fallback en VPS: función que llame a OpenAI cuando fallen créditos
- [ ] Tests del analyzer (mock de Bedrock con moto)
- [ ] Set de tests de prompt con casos conocidos
- [ ] **Capturar screenshots**: ejemplos de análisis IA generados, alertas con contexto

**Entregable**: el sistema detecta problemas y los explica en lenguaje natural. Tests verde.

---

### Semana 3 — Notificaciones y observabilidad (5–7 días)

- [ ] Crear topic SNS `ops-alerts`
- [ ] Configurar n8n en VPS para recibir SNS vía webhook (con secret token)
- [ ] Crear flujo en n8n: alerta → WhatsApp (Evolution API) con idempotencia
- [ ] Crear flujo en n8n: alerta → Slack (`#ops-alertas`) con Block Kit
- [ ] Implementar lógica de routing por severidad
- [ ] Crear regla EventBridge que dispare Lambda diaria a las 8am
- [ ] Lambda de reporte: arma PDF → S3 → envía link por email (SES)
- [ ] **Crear CloudWatch Dashboard** con métricas clave del sistema
- [ ] **Configurar CloudWatch Alarms** (errores > 5%, DLQ > 0, latencia, costo)
- [ ] Lambda que revisa DLQ diariamente y alerta si hay mensajes
- [ ] **Capturar screenshots**: alertas WhatsApp/Slack, dashboard CloudWatch, reporte PDF

**Entregable**: sistema completo de alertas con observabilidad real. Material visual potente para portafolio.

---

### Semana 4 — Dashboard en tiempo real (5–7 días)

- [ ] Crear Lambda `query` que expone KPIs y alertas vía API Gateway
- [ ] Configurar API Gateway con API key + rate limiting (100 req/min)
- [ ] Construir frontend Next.js: cards de KPIs, lista de alertas, gráficos
- [ ] Agregar gráficos con Recharts: ventas por hora, stock crítico, top productos
- [ ] Implementar auth básica del dashboard (API key inicial o Clerk)
- [ ] Tests del query Lambda
- [ ] Desplegar en Vercel con dominio propio o subdominio
- [ ] Validar flujo end-to-end completo
- [ ] (Opcional, si hay tiempo) Agregar chat IA al dashboard
- [ ] **Capturar screenshots/video del dashboard funcionando**

**Entregable**: link público (con auth) que cualquier reclutador puede abrir y ver funcionando.

---

### Semana 5 — IaC, CI/CD y presentación (5–7 días)

- [ ] Migrar toda la infraestructura AWS a Terraform con workspaces (`dev`, `prod`)
- [ ] Configurar IAM con mínimo privilegio (rol específico por Lambda)
- [ ] Workflow GitHub Actions: tests + lint + deploy de Lambdas en cada push
- [ ] Workflow GitHub Actions: `terraform plan` en PRs, `terraform apply` en main
- [ ] Migrar auth del dashboard a Cognito o Clerk
- [ ] Crear diagrama de arquitectura final (excalidraw o draw.io)
- [ ] Escribir README profesional: problema, solución, decisiones, demo
- [ ] Completar ADRs en `/docs/decisions/` (mínimo 5 decisiones documentadas)
- [ ] Grabar video demo de 2 minutos (problema → solución → resultado)
- [ ] Publicar post en LinkedIn con el video y arquitectura

**Entregable**: proyecto profesional, reproducible, documentado y listo para defender en entrevista.

---

## 12. Estructura del repositorio

```
opsropz/
├── README.md                       # Descripción completa con diagrama y demo
├── .pre-commit-config.yaml         # Hooks de calidad de código
├── .github/
│   └── workflows/
│       ├── ci.yml                  # Lint + tests + security scan
│       ├── deploy-lambdas.yml      # Deploy de Lambdas
│       └── terraform.yml           # Plan en PR, apply en main
├── docs/
│   ├── architecture.svg            # Diagrama de arquitectura
│   ├── decisions/                  # ADRs numerados
│   │   ├── 0001-hybrid-aws-vps.md
│   │   ├── 0002-claude-haiku-vs-gpt.md
│   │   ├── 0003-dlq-strategy.md
│   │   └── ...
│   └── screenshots/                # Capturas para README
├── lambdas/
│   ├── processor/
│   │   ├── handler.py
│   │   ├── requirements.txt
│   │   ├── tests/
│   │   └── README.md
│   ├── analyzer/
│   ├── query/
│   ├── daily_report/
│   └── dlq_monitor/
├── infra/
│   ├── main.tf                     # Recursos principales
│   ├── lambdas.tf                  # Funciones Lambda
│   ├── observability.tf            # CloudWatch dashboard + alarms
│   ├── iam.tf                      # Roles con mínimo privilegio
│   ├── variables.tf
│   ├── outputs.tf
│   └── environments/
│       ├── dev.tfvars
│       └── prod.tfvars
├── vps/
│   ├── simulator/
│   │   ├── main.py
│   │   └── tests/
│   ├── n8n-flows/                  # Flujos exportados de n8n
│   └── docker-compose.yml
└── dashboard/
    ├── app/                        # Next.js App Router
    ├── components/
    ├── lib/
    └── tests/
```

---

## 13. Cómo describirlo en el CV

### Entrada para sección de proyectos

**OpsRopz — Sistema de inteligencia operacional retail (AWS + IA generativa)**

- Diseñé arquitectura event-driven serverless con AWS Lambda, SQS (+ DLQ) y DynamoDB procesando eventos de inventario, ventas y pedidos en tiempo real, con correlation IDs end-to-end para trazabilidad completa.
- Integré Amazon Bedrock (Claude Haiku 4.5) con retries de backoff exponencial para análisis autónomo de KPIs operacionales y generación de alertas en lenguaje natural con recomendaciones accionables.
- Implementé sistema de routing inteligente con n8n que envía notificaciones idempotentes por WhatsApp, Slack y email según severidad — críticas a gerencia, operativas al equipo.
- Construí capa de observabilidad con CloudWatch Dashboards, structured logging JSON y alarmas automáticas sobre errores, latencia y costos.
- Provisioné infraestructura con Terraform IaC (workspaces dev/prod) e IAM de mínimo privilegio. CI/CD con GitHub Actions incluyendo tests, lint y security scanning.
- Dashboard Next.js protegido con autenticación y rate limiting, desplegado en Vercel. Diseñado para operar dentro de la capa gratuita de AWS.

### Pitch de 30 segundos para entrevista

> "Construí un sistema de inteligencia operacional serverless sobre AWS que monitorea inventario, ventas y pedidos de una tienda retail en tiempo real. Diseñé un pipeline event-driven desacoplado con SQS y Lambdas, usando severidad para enrutar alertas a distintos canales — WhatsApp para gerencia, Slack para el equipo. La IA es un componente, no el producto: detecta anomalías, las analiza en contexto y genera recomendaciones. Toda la infraestructura está como código en Terraform, con observabilidad completa en CloudWatch y tests automatizados en CI."

---

## 14. Regla de oro

> Cada semana termina con algo que funciona y puedes mostrar. Si en la Semana 2 ya detecta anomalías, graba un video corto explicándolo. El material visual semanal sirve para LinkedIn, README y portafolio mientras sigues construyendo.

---

## 15. Anti-patterns a evitar

- ❌ Convertirlo en "otro wrapper de OpenAI" — la IA es un componente del sistema, no el producto.
- ❌ Empezar por el dashboard bonito sin tener el pipeline funcionando primero.
- ❌ Saltar tests "por velocidad" — agregarlos después cuesta 10x más.
- ❌ Commitear secrets aunque sea por accidente (pre-commit hooks lo previenen).
- ❌ Permisos IAM amplios "para que funcione" — siempre mínimo privilegio.
- ❌ Esperar a tener todo perfecto antes de mostrarlo.

---

**Última actualización**: Mayo 2026
**Tiempo total estimado**: 5 semanas a medio tiempo
**Modelo de costo**: diseñado para operar dentro de la capa gratuita de AWS
