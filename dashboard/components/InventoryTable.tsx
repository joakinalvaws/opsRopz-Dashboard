import type { InventoryItem } from "@/lib/types";
import { classifyDays, STOCK_STATUS } from "@/lib/status";
import { timeAgo } from "@/lib/time";

export default function InventoryTable({ inventory }: { inventory: InventoryItem[] }) {
  if (inventory.length === 0) {
    return (
      <div className="text-slate-500 py-8 text-center">Sin datos de inventario todavía</div>
    );
  }

  return (
    <div className="max-h-[420px] overflow-y-auto">
      <table className="w-full text-sm">
        <thead className="sticky top-0 bg-slate-800 text-left text-xs uppercase tracking-wide text-slate-500">
          <tr>
            <th className="py-2 pr-3 font-medium">Estado</th>
            <th className="py-2 pr-3 font-medium">SKU</th>
            <th className="py-2 pr-3 font-medium">Tienda</th>
            <th className="py-2 pr-3 font-medium text-right">Stock</th>
            <th className="py-2 pr-3 font-medium text-right">Días</th>
            <th className="py-2 font-medium text-right">Actualizado</th>
          </tr>
        </thead>
        <tbody>
          {inventory.map((i) => {
            const s = STOCK_STATUS[classifyDays(i.days_of_stock)];
            return (
              <tr key={i.sku} className="border-t border-slate-800">
                <td className="py-2 pr-3">
                  <span
                    className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-xs ${s.badge}`}
                  >
                    <span className={`h-1.5 w-1.5 rounded-full ${s.dot}`} />
                    {s.label}
                  </span>
                </td>
                <td className="py-2 pr-3 font-mono text-slate-300">{i.sku}</td>
                <td className="py-2 pr-3 text-slate-400">{i.store_id}</td>
                <td className="py-2 pr-3 text-right text-slate-300">{i.current_stock ?? "—"}</td>
                <td className={`py-2 pr-3 text-right font-medium ${s.text}`}>
                  {i.days_of_stock ?? "s/d"}
                </td>
                <td className="py-2 text-right text-xs text-slate-500">{timeAgo(i.timestamp)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
