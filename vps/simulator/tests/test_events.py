import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from events import (
    generate_batch,
    make_inventory_snapshot,
    make_sale,
    make_supplier_order,
)

ENVELOPE_FIELDS = ("correlation_id", "event_type", "timestamp", "store_id", "sku", "payload")


def _assert_valid_envelope(event):
    for field in ENVELOPE_FIELDS:
        assert field in event, f"falta {field}"
    assert event["timestamp"].endswith("Z")
    assert isinstance(event["payload"], dict)


class TestGenerators:
    def test_inventory_snapshot_shape(self):
        ev = make_inventory_snapshot(random.Random(42))
        _assert_valid_envelope(ev)
        assert ev["event_type"] == "inventory_snapshot"
        assert ev["payload"]["current_stock"] >= 0
        assert ev["payload"]["avg_daily_sales"] > 0

    def test_sale_shape(self):
        ev = make_sale(random.Random(42))
        _assert_valid_envelope(ev)
        assert ev["event_type"] == "sale"
        assert ev["payload"]["units"] >= 1

    def test_supplier_order_shape(self):
        ev = make_supplier_order(random.Random(42))
        _assert_valid_envelope(ev)
        assert ev["event_type"] == "supplier_order"
        assert ev["payload"]["supplier"]


class TestDeterminism:
    def test_same_seed_same_output(self):
        a = generate_batch(5, random.Random(7))
        b = generate_batch(5, random.Random(7))
        assert a == b

    def test_correlation_ids_are_unique_in_batch(self):
        batch = generate_batch(50, random.Random(1))
        ids = [e["correlation_id"] for e in batch]
        assert len(set(ids)) == len(ids)


class TestGenerateBatch:
    def test_count(self):
        assert len(generate_batch(10)) == 10

    def test_all_valid(self):
        for ev in generate_batch(20, random.Random(99)):
            _assert_valid_envelope(ev)
