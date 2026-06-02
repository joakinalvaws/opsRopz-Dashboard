import os
import sys
from datetime import datetime, timezone
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import handler


def _inv(sku, dos):
    return {
        "sku": sku,
        "event_type": "inventory_snapshot",
        "days_of_stock": Decimal(str(dos)),
        "ingested_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def _sale(sku, qty=10):
    return {
        "sku": sku,
        "event_type": "sale",
        "quantity": Decimal(str(qty)),
        "ingested_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


class _FakeTable:
    def __init__(self, items):
        self._items = items

    def scan(self, **kw):
        return {"Items": self._items}


class _FakeDynamo:
    def __init__(self, items):
        self._items = items

    def Table(self, name):
        return _FakeTable(self._items)


class _FakeSES:
    def __init__(self):
        self.sent: list = []

    def send_email(self, **kw):
        self.sent.append(kw)


class _FakeSNS:
    def __init__(self):
        self.published: list = []

    def publish(self, **kw):
        self.published.append(kw)


def _setup(monkeypatch, items, sender="from@test.com", recipient="to@test.com"):
    ses = _FakeSES()
    sns = _FakeSNS()
    monkeypatch.setattr(handler, "_dynamo_resource", _FakeDynamo(items))
    monkeypatch.setattr(handler, "_ses_client", ses)
    monkeypatch.setattr(handler, "_sns_client", sns)
    monkeypatch.setattr(handler, "_TABLE_NAME", "test-table")
    monkeypatch.setattr(handler, "_SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123:test")
    monkeypatch.setattr(handler, "_SES_SENDER", sender)
    monkeypatch.setattr(handler, "_SES_RECIPIENT", recipient)
    return ses, sns


def test_sends_email_and_publishes_sns(monkeypatch):
    items = [_inv("SKU_A", 5), _sale("SKU_A")]
    ses, sns = _setup(monkeypatch, items)

    result = handler.lambda_handler({}, None)

    assert result == {"report_sent": True, "eventos_procesados": 2}
    assert len(ses.sent) == 1
    assert "Reporte diario" in ses.sent[0]["Message"]["Subject"]["Data"]
    assert len(sns.published) == 1


def test_critical_stock_appears_in_report(monkeypatch):
    ses, _ = _setup(monkeypatch, [_inv("LECHE_GLORIA", 1.5)])

    handler.lambda_handler({}, None)

    body = ses.sent[0]["Message"]["Body"]["Text"]["Data"]
    assert "LECHE_GLORIA" in body
    assert "STOCK CRÍTICO" in body
    assert "1.5" in body


def test_healthy_stock_shows_no_alerts(monkeypatch):
    ses, _ = _setup(monkeypatch, [_inv("SKU_OK", 15)])

    handler.lambda_handler({}, None)

    body = ses.sent[0]["Message"]["Body"]["Text"]["Data"]
    assert "Sin alertas críticas" in body
    assert "STOCK CRÍTICO" not in body


def test_skips_email_when_ses_not_configured(monkeypatch):
    ses, sns = _setup(monkeypatch, [], sender="", recipient="")

    result = handler.lambda_handler({}, None)

    assert result["report_sent"] is True
    assert ses.sent == []
    assert len(sns.published) == 1  # SNS sigue publicando aunque no haya SES


def test_total_sales_sum(monkeypatch):
    items = [_sale("A", 30), _sale("B", 20), _sale("A", 10)]
    ses, _ = _setup(monkeypatch, items)

    handler.lambda_handler({}, None)

    body = ses.sent[0]["Message"]["Body"]["Text"]["Data"]
    assert "60" in body  # 30 + 20 + 10


def test_sns_message_contains_stock_critical_count(monkeypatch):
    import json as _json

    items = [_inv("A", 1), _inv("B", 2), _inv("C", 10)]
    _, sns = _setup(monkeypatch, items)

    handler.lambda_handler({}, None)

    msg = _json.loads(sns.published[0]["Message"])
    assert msg["stock_critico_count"] == 2  # A y B < 3 días
    assert msg["severity"] == "info"
    assert msg["rule"] == "reporte_diario"
