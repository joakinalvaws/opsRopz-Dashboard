import { fetchFromApi } from "@/lib/api";

// Proxy server-side: el navegador llama aquí (mismo origen, sin key);
// este handler agrega la API key y consulta API Gateway.
export async function GET() {
  return fetchFromApi("/kpis");
}
