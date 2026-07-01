import type { InventoryItem } from "@/lib/types";

// Umbral real del backend: crítico si days_of_stock < 3 (lambdas/analyzer/anomalies.py).
// La banda "Atención" (3–7 días) es PURAMENTE visual del dashboard; el backend solo
// distingue crítico (<3) de no-crítico. Este módulo es la única fuente de verdad de
// umbrales y colores, reutilizada por el gráfico, las tarjetas KPI y la tabla.
export const DAYS_CRITICAL = 3;
export const DAYS_HEALTHY = 7;

export type StockStatus = "critico" | "atencion" | "saludable" | "sindato";

export function classifyDays(days: number | null | undefined): StockStatus {
  if (days === null || days === undefined) return "sindato";
  if (days < DAYS_CRITICAL) return "critico";
  if (days < DAYS_HEALTHY) return "atencion";
  return "saludable";
}

export interface StatusStyle {
  label: string;
  hex: string; // color para Recharts / SVG (no soporta clases Tailwind)
  text: string; // clase Tailwind de texto
  badge: string; // clase Tailwind para pill/badge
  dot: string; // clase Tailwind para punto de color
}

export const STOCK_STATUS: Record<StockStatus, StatusStyle> = {
  critico: {
    label: "Crítico",
    hex: "#dc2626",
    text: "text-critical",
    badge: "bg-critical/15 text-critical border-critical/40",
    dot: "bg-critical",
  },
  atencion: {
    label: "Atención",
    hex: "#f59e0b",
    text: "text-alert",
    badge: "bg-alert/15 text-alert border-alert/40",
    dot: "bg-alert",
  },
  saludable: {
    label: "Saludable",
    hex: "#10b981",
    text: "text-healthy",
    badge: "bg-healthy/15 text-healthy border-healthy/40",
    dot: "bg-healthy",
  },
  sindato: {
    label: "Sin dato",
    hex: "#64748b",
    text: "text-slate-400",
    badge: "bg-slate-700/40 text-slate-400 border-slate-600/50",
    dot: "bg-slate-500",
  },
};

export interface StatusCounts {
  critico: number;
  atencion: number;
  saludable: number;
  sindato: number;
  total: number;
}

export function countByStatus(inventory: InventoryItem[]): StatusCounts {
  const counts: StatusCounts = { critico: 0, atencion: 0, saludable: 0, sindato: 0, total: 0 };
  for (const item of inventory) {
    counts[classifyDays(item.days_of_stock)] += 1;
    counts.total += 1;
  }
  return counts;
}
