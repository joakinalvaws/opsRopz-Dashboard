import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from anomalies import ALERT, CRITICAL, Anomaly, evaluate  # noqa: E402


def _inv(days_of_stock):
    return {"event_type": "inventory_snapshot", "days_of_stock": days_of_stock, "sku": "X"}


class TestInventory:
    def test_critical_under_threshold(self):
        a = evaluate(_inv(1.5))
        assert isinstance(a, Anomaly)
        assert a.severity == CRITICAL
        assert a.rule == "stock_critico"

    def test_healthy_above_threshold(self):
        assert evaluate(_inv(10.0)) is None

    def test_exactly_threshold_is_healthy(self):
        assert evaluate(_inv(3.0)) is None

    def test_zero_days_is_critical(self):
        assert evaluate(_inv(0.0)).severity == CRITICAL

    def test_missing_days_of_stock_returns_none(self):
        assert evaluate({"event_type": "inventory_snapshot", "sku": "X"}) is None

    def test_decimal_string_value(self):
        # DynamoDB devuelve números como Decimal/str.
        assert evaluate(_inv("2.0")).severity == CRITICAL


class TestSale:
    def test_drop_alert(self):
        a = evaluate({"event_type": "sale", "sales_vs_average_pct": -35.0})
        assert a.severity == ALERT

    def test_severe_drop_critical(self):
        a = evaluate({"event_type": "sale", "sales_vs_average_pct": -70.0})
        assert a.severity == CRITICAL

    def test_normal_sales_none(self):
        assert evaluate({"event_type": "sale", "sales_vs_average_pct": 5.0}) is None

    def test_no_deviation_field_none(self):
        assert evaluate({"event_type": "sale", "units": 3}) is None


class TestOther:
    def test_unknown_event_type_none(self):
        assert evaluate({"event_type": "supplier_order", "sku": "X"}) is None

    def test_no_event_type_none(self):
        assert evaluate({"sku": "X"}) is None
