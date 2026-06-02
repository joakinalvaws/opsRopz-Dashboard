import { fetchFromApi } from "@/lib/api";

export async function GET() {
  return fetchFromApi("/alerts");
}
