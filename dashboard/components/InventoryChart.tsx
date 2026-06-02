"use client";

import {
  Bar,
  BarChart,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { InventoryItem } from "@/lib/types";

function barColor(days: number | null): string {
  if (days === null) return "#64748b";
  if (days < 3) return "#dc2626";
  if (days < 7) return "#f59e0b";
  return "#10b981";
}

export default function InventoryChart({ inventory }: { inventory: InventoryItem[] }) {
  const data = inventory
    .filter((i) => i.days_of_stock !== null)
    .slice(0, 12)
    .map((i) => ({ sku: i.sku, dias: i.days_of_stock as number }));

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-500">
        Sin datos de inventario todavía
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 40 }}>
        <XAxis
          dataKey="sku"
          angle={-35}
          textAnchor="end"
          interval={0}
          tick={{ fill: "#94a3b8", fontSize: 11 }}
        />
        <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} />
        <Tooltip
          contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
          labelStyle={{ color: "#e2e8f0" }}
          formatter={(v: number) => [`${v} días`, "Stock restante"]}
        />
        <Bar dataKey="dias" radius={[4, 4, 0, 0]}>
          {data.map((d, i) => (
            <Cell key={i} fill={barColor(d.dias)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
