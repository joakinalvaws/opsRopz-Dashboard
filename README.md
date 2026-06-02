# OpsRopz

> Sistema de inteligencia operacional para retail — AWS serverless + IA generativa.

OpsRopz monitorea las operaciones de una tienda retail en tiempo real, detecta
problemas automáticamente con IA generativa y notifica al equipo por WhatsApp,
Slack y email — sin que nadie tenga que revisar planillas o dashboards a mano.

En lugar de que los gerentes revisen reportes, **el sistema los busca a ellos
cuando algo necesita atención**, explicándolo en lenguaje natural con
recomendaciones accionables.

**🔗 Demo en vivo:** [opsropz-dashboard.vercel.app](https://opsropz-dashboard.vercel.app)
— KPIs de inventario y alertas generadas por IA, en tiempo real.

## Arquitectura

```
Eventos retail (VPS) → SQS → Lambda (processor) → DynamoDB (KPIs)
                       ↓DLQ              ↓
                                Lambda (analyzer) → Bedrock / Claude Haiku 4.5
                                          ↓
                                        SNS → CloudWatch
                                          ↓
                          n8n (VPS) → WhatsApp / Slack
                          SES → Email (reporte diario)
                                          ↓
                      API Gateway → Dashboard Next.js (Vercel)
```

Arquitectura híbrida: el núcleo event-driven corre serverless en AWS (dentro de
la capa gratuita), mientras los servicios 24/7 con estado (simulador, n8n,
WhatsApp, fallback LLM) corren en un VPS. Ver
[ADR-0001](docs/decisions/0001-hybrid-aws-vps.md).

## Stack

| Capa | Tecnología |
|---|---|
| Backend / eventos | Python 3.12, AWS Lambda, SQS (+DLQ), DynamoDB, SNS, EventBridge, SES, S3 |
| IA | Amazon Bedrock — Claude Haiku 4.5 vía inference profile `us.anthropic.claude-haiku-4-5-20251001-v1:0`, con fallback a API externa en VPS |
| Frontend | Next.js 15, Recharts, Tailwind CSS (Vercel) |
| Orquestación | n8n, Evolution API (WhatsApp), Slack API |
| Infraestructura | Terraform + workspaces (dev/prod) |
| CI/CD | GitHub Actions, pre-commit hooks |
| Observabilidad | CloudWatch Dashboards + Logs Insights, correlation IDs |
| Testing | pytest, moto (mocks AWS), pip-audit |

## Estructura del repositorio

```
opsropz/
├── lambdas/        # Funciones Lambda (processor, analyzer, query, daily_report, dlq_monitor)
├── infra/          # Terraform: recursos AWS, IAM, observabilidad
├── vps/            # Simulador Python + flujos n8n + docker-compose
├── dashboard/      # Frontend Next.js
└── docs/           # ADRs, diagrama de arquitectura, screenshots
```

## Estado del proyecto

Plan de 5 semanas a medio tiempo. Progreso:

- [x] **Semana 0** — Setup del repo, pre-commit, CI inicial, skeleton de Terraform, ADRs
- [x] **Semana 1** — Pipeline event-driven (SQS → Lambda → DynamoDB) + simulador, desplegado en AWS
- [x] **Semana 2** — Capa de IA: analyzer (DynamoDB Streams → Bedrock Claude Haiku 4.5), detección de anomalías, 59 tests, 94% cobertura. Desplegado y validado end-to-end — [ver ejemplos de alertas IA](docs/screenshots/sample-alerts.md)
- [x] **Semana 3** — Notificaciones (SNS → n8n → WhatsApp/Slack con routing por severidad) + reporte diario (EventBridge → SES), CloudWatch Dashboard + alarmas, dlq_monitor. Verificado end-to-end.
- [x] **Semana 4** — Dashboard en tiempo real (Next.js + API Gateway con API key) — [en vivo](https://opsropz-dashboard.vercel.app). Lambda `query`, tabla de alertas, proxy server-side ([ADR-0004](docs/decisions/0004-dashboard-server-side-api-key.md)).
- [ ] **Semana 5** — CI/CD (Terraform en GitHub Actions), documentación final, video demo

**78 tests** verdes (processor, analyzer, dlq_monitor, daily_report, query, simulator).

## Desarrollo local

```bash
# Setup de herramientas de dev
pip install -r requirements-dev.txt
pre-commit install

# Lint + tests
ruff check .
pytest --cov

# Terraform (validación sin backend)
terraform -chdir=infra init -backend=false
terraform -chdir=infra validate
```

## Decisiones de arquitectura

Las decisiones técnicas relevantes están documentadas en
[`docs/decisions/`](docs/decisions/):

- [0001 — Arquitectura híbrida AWS + VPS](docs/decisions/0001-hybrid-aws-vps.md)
- [0002 — SSM Parameter Store en lugar de Secrets Manager](docs/decisions/0002-ssm-over-secrets-manager.md)
- [0003 — Resiliencia: DLQ + fallos parciales de batch](docs/decisions/0003-dlq-batch-failures.md)
- [0004 — Dashboard público con proxy server-side de la API key](docs/decisions/0004-dashboard-server-side-api-key.md)
- [0005 — Claude Haiku 4.5 vía inference profile](docs/decisions/0005-claude-haiku-inference-profile.md)
