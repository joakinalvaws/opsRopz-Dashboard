# OpsRopz Dashboard

Dashboard en tiempo real (Next.js 15 + Recharts) que muestra KPIs de inventario y el
historial de alertas. Consume el API Gateway de OpsRopz vía un proxy server-side para
que la API key **nunca llegue al navegador**.

## Arquitectura de seguridad

```
Navegador → /api/kpis (Next route handler) → [API key server-side] → API Gateway → Lambda query
```

El navegador llama a rutas del mismo origen (`/api/kpis`, `/api/alerts`). Esas rutas
corren en el servidor de Next.js (Vercel), agregan la `DASHBOARD_API_KEY` desde una env
var y consultan API Gateway. La key vive solo en el servidor.

## Variables de entorno

| Variable | Origen | Notas |
|---|---|---|
| `DASHBOARD_API_URL` | `terraform output dashboard_api_url` | URL base del API Gateway |
| `DASHBOARD_API_KEY` | `terraform output -raw dashboard_api_key` | Sensible. **Sin** prefijo `NEXT_PUBLIC` |

## Desarrollo local

```bash
cp .env.example .env   # y completar con los outputs de Terraform
npm install
npm run dev            # http://localhost:3000
```

## Deploy en Vercel

1. `npm i -g vercel` (o usar la UI de Vercel)
2. Desde `dashboard/`: `vercel` (link del proyecto)
3. Configurar las 2 env vars en el proyecto (Settings → Environment Variables):
   - `DASHBOARD_API_URL`
   - `DASHBOARD_API_KEY`
4. `vercel --prod`

El dashboard hace auto-refresh cada 30s para dar sensación de tiempo real.
