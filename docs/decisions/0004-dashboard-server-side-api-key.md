# 0004 — Dashboard público con proxy server-side de la API key

- **Estado**: Aceptada
- **Fecha**: 2026-06-02

## Contexto

El dashboard (Next.js en Vercel) debe consumir el API Gateway de OpsRopz, que
está protegido con una **API key**. Surge la tensión clásica:

- Si el navegador llama directo a API Gateway, la API key viaja al cliente y
  **queda expuesta** (en el bundle JS o en las requests del Network tab).
- Por otro lado, el objetivo de portafolio es que **cualquier reclutador pueda
  abrir el link sin credenciales** — un muro de login (Clerk/Cognito) lo impediría.

## Decisión

Usar un **proxy server-side** dentro del propio Next.js:

- El navegador llama a rutas del mismo origen: `/api/kpis`, `/api/alerts`
  (route handlers en `dashboard/app/api/*`).
- Esas rutas corren en el **servidor de Vercel**, leen `DASHBOARD_API_KEY` de una
  env var (sin prefijo `NEXT_PUBLIC`) y reenvían la petición a API Gateway con la
  key en el header `x-api-key`.
- La key vive solo en el servidor; **nunca llega al navegador**.

La autenticación de usuario (Clerk/Cognito) se posterga: el dashboard es de solo
lectura y público a propósito. El rate limiting del usage plan de API Gateway
acota el abuso.

## Consecuencias

**Positivas**
- Link público abrible por cualquiera, sin exponer secretos (verificado: la key
  no aparece en el HTML servido).
- La capa de auth real puede añadirse después sin tocar el patrón de datos.
- El rate limiting protege la cuota de la capa gratuita.

**Negativas**
- Toda lectura pasa por el server de Vercel (un hop extra). Para este volumen es
  irrelevante.
- El dashboard no distingue usuarios. Aceptable: no hay datos por-usuario ni
  acciones de escritura.

## Alternativas descartadas

- **API key en el cliente** (`NEXT_PUBLIC_*`): expone el secreto. Descartada.
- **Clerk/Cognito desde ya**: muro de login que impide la demo de portafolio.
  Se mantiene como evolución futura (Semana 5+) si el dashboard gana escrituras.
