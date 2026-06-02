// Helper server-side: llama al API Gateway con la API key desde env vars.
// Solo se importa desde route handlers (server). La key nunca se expone al cliente.

const API_URL = process.env.DASHBOARD_API_URL;
const API_KEY = process.env.DASHBOARD_API_KEY;

export async function fetchFromApi(path: string): Promise<Response> {
  if (!API_URL || !API_KEY) {
    return Response.json(
      { error: "API no configurada (faltan DASHBOARD_API_URL / DASHBOARD_API_KEY)" },
      { status: 503 },
    );
  }

  const upstream = await fetch(`${API_URL}${path}`, {
    headers: { "x-api-key": API_KEY },
    // KPIs y alertas cambian seguido: sin cache, datos frescos.
    cache: "no-store",
  });

  const body = await upstream.text();
  return new Response(body, {
    status: upstream.status,
    headers: { "Content-Type": "application/json" },
  });
}
