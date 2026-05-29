import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kpis import days_of_stock, sales_vs_average_pct, stock_drop_pct  # noqa: E402


class TestDaysOfStock:
    def test_normal(self):
        assert days_of_stock(72, 48) == 1.5

    def test_rounds_to_two_decimals(self):
        assert days_of_stock(100, 3) == 33.33

    def test_zero_sales_returns_none(self):
        assert days_of_stock(50, 0) is None

    def test_negative_sales_returns_none(self):
        assert days_of_stock(50, -5) is None

    def test_negative_stock_returns_none(self):
        assert days_of_stock(-10, 5) is None

    def test_zero_stock_is_zero_days(self):
        assert days_of_stock(0, 48) == 0.0


class TestStockDropPct:
    def test_drop(self):
        assert stock_drop_pct(100, 60) == 40.0

    def test_increase_is_negative(self):
        assert stock_drop_pct(50, 75) == -50.0

    def test_no_previous_base_returns_none(self):
        assert stock_drop_pct(0, 10) is None


class TestSalesVsAveragePct:
    def test_below_average(self):
        assert sales_vs_average_pct(70, 100) == -30.0

    def test_above_average(self):
        assert sales_vs_average_pct(150, 100) == 50.0

    def test_no_average_returns_none(self):
        assert sales_vs_average_pct(100, 0) is None
