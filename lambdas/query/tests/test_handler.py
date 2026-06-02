import json
import os
import sys
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import handler


class _FakeTable:
    def __init__(self, scan_items=None, query_items=None):
        self._scan_items = scan_items or []
        self._query_items = query_items or []
        self.last_query_kwargs = None

    def scan(self, **kw):
        return {"Items": self._scan_items}

    def query(self, **kw):
        self.last_query_kwargs = kw
        return {"Items": self._query_items}


class _FakeDynamo:
    def __init__(self, table):
        self._table = table

    def Table(self, name):
        return self._table


def _inv(sku, dos, event_id, stock=100):
    return {
        "sku": sku,
        "event_type": "inventory_snapshot",
        "days_of_stock": Decimal(str(dos)),
        "current_stock": Decimal(str(stock)),
        "event_id": event_id,
        "store_id": "lima",
        "timestamp": event_id.split("#")[0],
    }


def _sale(sku):
    return {"sku": sku, "event_type": "sale", "event_id": "2026-06-01#x"}


def _setup(monkeypatch, table):
    monkeypatch.setattr(handler, "_dynamo", _FakeDynamo(table))
    monkeypatch.setattr(handler, "_OPERATIONS_TABLE", "ops")
    monkeypatch.setattr(handler, "_ALERTS_TABLE", "alerts")


def test_kpis_returns_latest_inventory_per_sku(monkeypatch):
    items = [
        _inv("SKU_A", 10, "2026-06-01T08:00:00Z#c1"),
        _inv("SKU_A", 2, "2026-06-01T12:00:00Z#c2"),  # más reciente
        _inv("SKU_B", 20, "2026-06-01T09:00:00Z#c3"),
        _sale("SKU_A"),
    ]
    _setup(monkeypatch, _FakeTable(scan_items=items))

    resp = handler.lambda_handler({"path": "/kpis"}, None)
    body = json.loads(resp["body"])

    assert resp["statusCode"] == 200
    assert body["skus_tracked"] == 2
    assert body["sales_events"] == 1
    # SKU_A debe reflejar el snapshot más reciente (2 días)
    sku_a = next(i for i in body["inventory"] if i["sku"] == "SKU_A")
    assert sku_a["days_of_stock"] == 2


def test_kpis_critical_count(monkeypatch):
    items = [
        _inv("A", 1, "2026-06-01T08:00:00Z#1"),
        _inv("B", 2.5, "2026-06-01T08:00:00Z#2"),
        _inv("C", 10, "2026-06-01T08:00:00Z#3"),
    ]
    _setup(monkeypatch, _FakeTable(scan_items=items))

    body = json.loads(handler.lambda_handler({"path": "/kpis"}, None)["body"])

    assert body["critical_count"] == 2  # A y B < 3 días


def test_kpis_inventory_sorted_critical_first(monkeypatch):
    items = [
        _inv("OK", 15, "2026-06-01T08:00:00Z#1"),
        _inv("CRIT", 1, "2026-06-01T08:00:00Z#2"),
    ]
    _setup(monkeypatch, _FakeTable(scan_items=items))

    body = json.loads(handler.lambda_handler({"path": "/kpis"}, None)["body"])

    assert body["inventory"][0]["sku"] == "CRIT"  # menor stock primero


def test_alerts_returns_recent_descending(monkeypatch):
    alerts = [
        {"sku": "A", "severity": "critico", "rule": "stock_critico", "analysis": "x",
         "correlation_id": "c1", "created_at": "2026-06-01T12:00:00Z"},
    ]
    table = _FakeTable(query_items=alerts)
    _setup(monkeypatch, table)

    resp = handler.lambda_handler({"path": "/alerts"}, None)
    body = json.loads(resp["body"])

    assert resp["statusCode"] == 200
    assert len(body["alerts"]) == 1
    assert body["alerts"][0]["sku"] == "A"
    # Debe pedir orden descendente (más recientes primero)
    assert table.last_query_kwargs["ScanIndexForward"] is False


def test_unknown_path_returns_404(monkeypatch):
    _setup(monkeypatch, _FakeTable())

    resp = handler.lambda_handler({"path": "/otra"}, None)

    assert resp["statusCode"] == 404


def test_decimal_serialized_to_number(monkeypatch):
    items = [_inv("A", 2.5, "2026-06-01T08:00:00Z#1", stock=72)]
    _setup(monkeypatch, _FakeTable(scan_items=items))

    body = handler.lambda_handler({"path": "/kpis"}, None)["body"]

    # No debe contener 'Decimal' y debe parsear como JSON válido
    assert "Decimal" not in body
    parsed = json.loads(body)
    assert parsed["inventory"][0]["current_stock"] == 72


def test_cors_header_present(monkeypatch):
    _setup(monkeypatch, _FakeTable())

    resp = handler.lambda_handler({"path": "/alerts"}, None)

    assert resp["headers"]["Access-Control-Allow-Origin"] == "*"
