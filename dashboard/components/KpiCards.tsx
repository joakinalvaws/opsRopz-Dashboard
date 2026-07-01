import type { KpisResponse } from "@/lib/types";
import { countByStatus, STOCK_STATUS } from "@/lib/status";

function Card({
  label,
  value,
  accent,
  dot,
  caption,
}: {
  label: string;
  value: number | string;
  accent: string;
  dot?: string;
  caption?: string;
}) {
  return (
    <div className="rounded-xl bg-slate-800/60 border border-slate-700 p-5">
      <div className="flex items-center gap-2 text-sm text-slate-400">
        {dot && <span className={`h-2 w-2 rounded-full ${dot}`} />}
        {label}
      </div>
      <div className={`mt-2 text-3xl font-bold ${accent}`}>{value}</div>
      {caption && <div className="mt-1 text-xs text-slate-500">{caption}</div>}
    </div>
  );
}

export default function KpiCards({ kpis }: { kpis: KpisResponse | null }) {
  const counts = countByStatus(kpis?.inventory ?? []);

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <Card
        label="SKUs monitoreados"
        value={kpis ? kpis.skus_tracked : "—"}
        accent="text-slate-100"
        caption={kpis ? `${kpis.sales_events} eventos de venta` : undefined}
      />
      <Card
        label="Crítico"
        value={kpis ? counts.critico : "—"}
        accent={counts.critico > 0 ? STOCK_STATUS.critico.text : "text-slate-100"}
        dot={STOCK_STATUS.critico.dot}
        caption="< 3 días de stock"
      />
      <Card
        label="Atención"
        value={kpis ? counts.atencion : "—"}
        accent={counts.atencion > 0 ? STOCK_STATUS.atencion.text : "text-slate-100"}
        dot={STOCK_STATUS.atencion.dot}
        caption="3–7 días de stock"
      />
      <Card
        label="Saludable"
        value={kpis ? counts.saludable : "—"}
        accent={counts.saludable > 0 ? STOCK_STATUS.saludable.text : "text-slate-100"}
        dot={STOCK_STATUS.saludable.dot}
        caption="≥ 7 días de stock"
      />
    </div>
  );
}
