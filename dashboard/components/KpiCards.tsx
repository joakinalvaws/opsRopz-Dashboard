import type { KpisResponse } from "@/lib/types";

function Card({ label, value, accent }: { label: string; value: number | string; accent: string }) {
  return (
    <div className="rounded-xl bg-slate-800/60 border border-slate-700 p-5">
      <div className="text-sm text-slate-400">{label}</div>
      <div className={`mt-2 text-3xl font-bold ${accent}`}>{value}</div>
    </div>
  );
}

export default function KpiCards({ kpis }: { kpis: KpisResponse | null }) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <Card label="SKUs monitoreados" value={kpis?.skus_tracked ?? "—"} accent="text-slate-100" />
      <Card
        label="Stock crítico"
        value={kpis?.critical_count ?? "—"}
        accent={kpis && kpis.critical_count > 0 ? "text-critical" : "text-emerald-400"}
      />
      <Card label="Eventos de venta" value={kpis?.sales_events ?? "—"} accent="text-info" />
      <Card
        label="Estado"
        value={kpis ? (kpis.critical_count > 0 ? "Atención" : "OK") : "—"}
        accent={kpis && kpis.critical_count > 0 ? "text-alert" : "text-emerald-400"}
      />
    </div>
  );
}
