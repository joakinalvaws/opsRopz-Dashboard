import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from normalize import InvalidEventError, build_item  # noqa: E402


def _inventory_event(**overrides):
    event = {
        "correlation_id": "abc-123",
        "event_type": "inventory_snapshot",
        "timestamp": "2026-05-29T14:30:00Z",
        "store_id": "lima-centro",
        "sku": "LECHE_GLORIA_1L",
        "payload": {"current_stock": 72, "avg_daily_sales": 48.0},
    }
    event.update(overrides)
    return event


class TestBuildItem:
    def test_inventory_computes_days_of_stock(self):
        item = build_item(_inventory_event())
        assert item["days_of_stock"] == 1.5
        assert item["sku"] == "LECHE_GLORIA_1L"
        assert item["correlation_id"] == "abc-123"
        assert "ingested_at" in item

    def test_event_id_combines_timestamp_and_correlation(self):
        item = build_item(_inventory_event())
        assert item["event_id"] == "2026-05-29T14:30:00Z#abc-123"

    def test_same_event_yields_same_event_id(self):
        # Idempotencia: mismo evento → misma clave → sobrescribe.
        assert build_item(_inventory_event())["event_id"] == build_item(_inventory_event())["event_id"]

    def test_payload_fields_are_merged(self):
        item = build_item(_inventory_event())
        assert item["current_stock"] == 72
        assert item["avg_daily_sales"] == 48.0

    def test_missing_field_raises(self):
        event = _inventory_event()
        del event["sku"]
        with pytest.raises(InvalidEventError):
            build_item(event)

    def test_empty_correlation_id_raises(self):
        with pytest.raises(InvalidEventError):
            build_item(_inventory_event(correlation_id=""))

    def test_no_days_of_stock_when_no_sales(self):
        item = build_item(_inventory_event(payload={"current_stock": 10, "avg_daily_sales": 0}))
        assert "days_of_stock" not in item

    def test_non_inventory_event_skips_kpi(self):
        event = {
            "correlation_id": "x",
            "event_type": "sale",
            "timestamp": "2026-05-29T14:30:00Z",
            "sku": "ARROZ_COSTENO_5KG",
            "payload": {"units": 3, "total": 13.5},
        }
        item = build_item(event)
        assert "days_of_stock" not in item
        assert item["units"] == 3
        assert item["store_id"] == "unknown"
