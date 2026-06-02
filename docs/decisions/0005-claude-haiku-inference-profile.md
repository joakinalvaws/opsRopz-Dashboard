# 0005 — Claude Haiku 4.5 vía inference profile para el análisis IA

- **Estado**: Aceptada
- **Fecha**: 2026-05-29

## Contexto

El analyzer necesita un LLM que, dado un KPI anómalo, genere una explicación en
lenguaje natural con recomendación accionable. Requisitos:

- **Costo bajo**: se invoca por cada anomalía detectada; el volumen puede crecer.
- **Latencia baja**: corre dentro de una Lambda con timeout de 30s.
- **Calidad suficiente**: el output va directo a un gerente por WhatsApp/Slack.
- **Dentro de AWS**: para usar los créditos iniciales de Bedrock y mantener IAM y
  observabilidad unificados.

## Decisión

Usar **Amazon Bedrock con Claude Haiku 4.5**, invocado a través de un **inference
profile** regional (`us.anthropic.claude-haiku-4-5-20251001-v1:0`).

- Haiku es el modelo más barato y rápido de la familia, suficiente para texto
  corto y estructurado.
- Claude Haiku 4.5 **exige invocarse vía inference profile**, no por el model ID
  directo. El profile `us.*` abarca varias regiones (us-east-1, us-east-2,
  us-west-2), así que el permiso IAM `bedrock:InvokeModel` debe cubrir tanto el
  ARN del **inference-profile** como el del **foundation-model** en cada región
  que el profile abarca (ver `infra/iam.tf`, `var.bedrock_profile_regions`).
- Retries con backoff exponencial para absorber throttling temporal sin tumbar
  la Lambda.

## Consecuencias

**Positivas**
- Costo y latencia mínimos para el caso de uso.
- Análisis IA dentro del mismo plano AWS (créditos, IAM, CloudWatch).

**Negativas**
- El requisito del inference profile complica los permisos IAM (hay que listar el
  FM por región). Documentado en variables de Terraform para que sea explícito.
- Dependencia de créditos Bedrock. Mitigada por el fallback LLM en VPS
  (ver [0001](0001-hybrid-aws-vps.md)) cuando se agoten.

## Alternativas descartadas

- **GPT-4o-mini / OpenAI directo**: saca el análisis del plano AWS y de los
  créditos Bedrock. Se reserva como **fallback** en el VPS, no como primario.
- **Claude Sonnet**: mejor calidad pero mayor costo y latencia, innecesario para
  alertas de texto corto.
