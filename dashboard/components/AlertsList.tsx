import type { Alert, Severity } from "@/lib/types";

const SEVERITY_STYLE: Record<Severity, { badge: string; label: string; icon: string }> = {
  critico: { badge: "bg-critical/20 text-critical border-critical/40", label: "Crítico", icon: "🚨" },
  alerta: { badge: "bg-alert/20 text-alert border-alert/40", label: "Alerta", icon: "⚠️" },
  info: { badge: "bg-info/20 text-info border-info/40", label: "Info", icon: "📊" },
};

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "ahora";
  if (mins < 60) return `hace ${mins} min`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `hace ${hours} h`;
  return `hace ${Math.floor(hours / 24)} d`;
}

export default function AlertsList({ alerts }: { alerts: Alert[] }) {
  if (alerts.length === 0) {
    return <div className="text-slate-500 py-8 text-center">Sin alertas registradas</div>;
  }

  return (
    <ul className="space-y-3">
      {alerts.map((a) => {
        const style = SEVERITY_STYLE[a.severity] ?? SEVERITY_STYLE.info;
        return (
          <li
            key={a.correlation_id + a.created_at}
            className="rounded-lg bg-slate-800/40 border border-slate-700 p-4"
          >
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span>{style.icon}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full border ${style.badge}`}>
                  {style.label}
                </span>
                <span className="font-mono text-sm text-slate-300">{a.sku}</span>
              </div>
              <span className="text-xs text-slate-500">{timeAgo(a.created_at)}</span>
            </div>
            <p className="mt-2 text-sm text-slate-300 leading-relaxed">{a.analysis}</p>
            <div className="mt-2 text-xs text-slate-600 font-mono">Ref: {a.correlation_id}</div>
          </li>
        );
      })}
    </ul>
  );
}
