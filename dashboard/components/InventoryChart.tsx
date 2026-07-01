"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { InventoryItem } from "@/lib/types";
import {
  classifyDays,
  DAYS_CRITICAL,
  DAYS_HEALTHY,
  STOCK_STATUS,
  type StockStatus,
} from "@/lib/status";

interface Datum {
  sku: string;
  dias: number;
  stock: number | null;
  store: string;
  status: StockStatus;
}

function CustomTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: { payload: Datum }[];
}) {
  if (!active || !payload || payload.length === 0) return null;
  const d = payload[0].payload;
  const style = STOCK_STATUS[d.status];
  return (
    <div className="rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-xs shadow-lg">
      <div className="font-mono text-sm text-slate-100">{d.sku}</div>
      <div className="mt-1 flex items-center gap-1.5">
        <span className={`h-2 w-2 rounded-full ${style.dot}`} />
        <span className={style.text}>{style.label}</span>
      </div>
      <dl className="mt-1.5 space-y-0.5 text-slate-300">
        <div className="flex justify-between gap-6">
          <dt className="text-slate-500">Días de stock</dt>
          <dd>{d.dias}</dd>
        </div>
        {d.stock !== null && (
          <div className="flex justify-between gap-6">
            <dt className="text-slate-500">Stock actual</dt>
            <dd>{d.stock} u.</dd>
          </div>
        )}
        <div className="flex justify-between gap-6">
          <dt className="text-slate-500">Tienda</dt>
          <dd>{d.store}</dd>
        </div>
      </dl>
    </div>
  );
}

function LegendChip({ status }: { status: StockStatus }) {
  const s = STOCK_STATUS[status];
  return (
    <span className="flex items-center gap-1.5 text-xs text-slate-400">
      <span className={`h-2.5 w-2.5 rounded-sm ${s.dot}`} />
      {s.label}
    </span>
  );
}

export default function InventoryChart({ inventory }: { inventory: InventoryItem[] }) {
  const data: Datum[] = inventory
    .filter((i) => i.days_of_stock !== null)
    .slice(0, 15)
    .map((i) => ({
      sku: i.sku,
      dias: i.days_of_stock as number,
      stock: i.current_stock,
      store: i.store_id,
      status: classifyDays(i.days_of_stock),
    }));

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-500">
        Sin datos de inventario todavía
      </div>
    );
  }

  return (
    <div>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} margin={{ top: 12, right: 16, left: -8, bottom: 48 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
          <XAxis
            dataKey="sku"
            angle={-35}
            textAnchor="end"
            interval={0}
            tick={{ fill: "#94a3b8", fontSize: 11 }}
          />
          <YAxis
            tick={{ fill: "#94a3b8", fontSize: 11 }}
            label={{
              value: "días",
              angle: -90,
              position: "insideLeft",
              fill: "#64748b",
              fontSize: 11,
              dy: 16,
            }}
          />
          <Tooltip cursor={{ fill: "rgba(148,163,184,0.08)" }} content={<CustomTooltip />} />
          <ReferenceLine
            y={DAYS_CRITICAL}
            stroke={STOCK_STATUS.critico.hex}
            strokeDasharray="4 4"
            label={{
              value: `Crítico ${DAYS_CRITICAL}d`,
              position: "insideTopRight",
              fill: STOCK_STATUS.critico.hex,
              fontSize: 10,
            }}
          />
          <ReferenceLine
            y={DAYS_HEALTHY}
            stroke={STOCK_STATUS.saludable.hex}
            strokeDasharray="4 4"
            label={{
              value: `Saludable ${DAYS_HEALTHY}d`,
              position: "insideTopRight",
              fill: STOCK_STATUS.saludable.hex,
              fontSize: 10,
            }}
          />
          <Bar dataKey="dias" radius={[4, 4, 0, 0]}>
            {data.map((d, i) => (
              <Cell key={i} fill={STOCK_STATUS[d.status].hex} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1">
        <LegendChip status="critico" />
        <LegendChip status="atencion" />
        <LegendChip status="saludable" />
      </div>
    </div>
  );
}
