"use client";

import { useCallback, useEffect, useState } from "react";
import KpiCards from "@/components/KpiCards";
import InventoryChart from "@/components/InventoryChart";
import InventoryTable from "@/components/InventoryTable";
import AlertsList from "@/components/AlertsList";
import type { AlertsResponse, KpisResponse } from "@/lib/types";

const REFRESH_MS = 30000;

export default function Dashboard() {
  const [kpis, setKpis] = useState<KpisResponse | null>(null);
  const [alerts, setAlerts] = useState<AlertsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null);

  const load = useCallback(async () => {
    try {
      const [k, a] = await Promise.all([
        fetch("/api/kpis").then((r) => r.json()),
        fetch("/api/alerts").then((r) => r.json()),
      ]);
      if (k.error) throw new Error(k.error);
      setKpis(k);
      setAlerts(a);
      setError(null);
      setUpdatedAt(new Date());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar datos");
    }
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, REFRESH_MS);
    return () => clearInterval(id);
  }, [load]);

  return (
    <main className="max-w-6xl mx-auto px-5 py-8">
      <header className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-slate-700 bg-gradient-to-br from-emerald-500/20 to-info/20 text-lg">
            📦
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-100">OpsRopz</h1>
            <p className="text-sm text-slate-400">Inteligencia operacional retail — en vivo</p>
          </div>
        </div>
        <div className="text-right text-xs text-slate-500">
          <div className="flex items-center gap-2 justify-end">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
            <span>Auto-refresh 30s</span>
          </div>
          {updatedAt && <div className="mt-1">Actualizado {updatedAt.toLocaleTimeString("es-PE")}</div>}
        </div>
      </header>

      {error && (
        <div className="mb-6 rounded-lg bg-critical/10 border border-critical/30 text-critical px-4 py-3 text-sm">
          {error}
        </div>
      )}

      <section className="mb-6">
        <KpiCards kpis={kpis} />
      </section>

      <section className="mb-6 rounded-xl bg-slate-800/30 border border-slate-700 p-5">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-300">
            Salud del inventario — días de stock por SKU
          </h2>
          <span className="text-xs text-slate-500">{kpis?.inventory.length ?? 0} SKUs</span>
        </div>
        <InventoryChart inventory={kpis?.inventory ?? []} />
      </section>

      <div className="grid lg:grid-cols-2 gap-6">
        <section className="rounded-xl bg-slate-800/30 border border-slate-700 p-5">
          <h2 className="text-sm font-semibold text-slate-300 mb-4">Detalle de inventario</h2>
          <InventoryTable inventory={kpis?.inventory ?? []} />
        </section>

        <section className="rounded-xl bg-slate-800/30 border border-slate-700 p-5">
          <h2 className="text-sm font-semibold text-slate-300 mb-4">Alertas recientes</h2>
          <AlertsList alerts={alerts?.alerts ?? []} />
        </section>
      </div>

      <footer className="mt-10 text-center text-xs text-slate-600">
        OpsRopz · AWS serverless + IA generativa (Claude Haiku 4.5)
      </footer>
    </main>
  );
}
