# 0002 — SSM Parameter Store en lugar de Secrets Manager

- **Estado**: Aceptada
- **Fecha**: 2026-05-28

## Contexto

El sistema necesita almacenar credenciales de forma segura: API key del
fallback LLM (OpenAI/Claude API), token del webhook de Slack, credenciales de
Evolution API y el secret del webhook SNS → n8n.

El plan original proponía **AWS Secrets Manager**. Sin embargo, Secrets Manager
solo es gratuito durante un **trial de 30 días**; después cuesta ~$0.40 por
secreto al mes. Con 4+ secretos, eso rompe el objetivo de operar dentro de la
capa gratuita.

## Decisión

Usar **AWS Systems Manager Parameter Store** con parámetros de tipo
`SecureString` (cifrados con la KMS key gestionada por AWS, `aws/ssm`).

- Los parámetros estándar son **siempre gratuitos** (hasta 10.000).
- La integración con Lambda es idéntica en la práctica: una llamada
  `ssm.get_parameter(Name=..., WithDecryption=True)`.
- Se nombran con jerarquía por entorno: `/opsropz/{env}/slack_webhook`, etc.

## Consecuencias

**Positivas**
- Costo cero, alineado con el objetivo de capa gratuita.
- Misma seguridad práctica (cifrado en reposo + IAM de mínimo privilegio).

**Negativas**
- Parameter Store no rota secretos automáticamente como Secrets Manager. Para
  este proyecto la rotación es manual, lo cual es aceptable.

## Cómo aplicarlo

- En `infra/iam.tf`, cada rol de Lambda recibe `ssm:GetParameter` **solo** sobre
  el prefijo `/opsropz/{env}/*` que necesita (mínimo privilegio).
- En código, leer el secreto al inicio del handler y cachearlo en memoria entre
  invocaciones (las Lambdas reutilizan el contexto en warm starts).
