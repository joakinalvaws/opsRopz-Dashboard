export interface InventoryItem {
  sku: string;
  days_of_stock: number | null;
  current_stock: number | null;
  store_id: string;
  timestamp: string;
}

export interface KpisResponse {
  skus_tracked: number;
  critical_count: number;
  sales_events: number;
  inventory: InventoryItem[];
}

export type Severity = "critico" | "alerta" | "info";

export interface Alert {
  sku: string;
  severity: Severity;
  rule: string;
  analysis: string;
  correlation_id: string;
  created_at: string;
}

export interface AlertsResponse {
  alerts: Alert[];
}
