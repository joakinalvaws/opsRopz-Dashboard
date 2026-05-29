import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bedrock_client  # noqa: E402
import handler  # noqa: E402
from bedrock_client import BedrockError  # noqa: E402


def _stream_event(*images, event_name="INSERT"):
    records = []
    for i, img in enumerate(images):
        records.append(
            {"eventName": event_name, "dynamodb": {"SequenceNumber": str(i), "NewImage": img}}
        )
    return {"Records": records}


def _critical_inventory_image():
    return {
        "sku": {"S": "LECHE_GLORIA_1L"},
        "event_type": {"S": "inventory_snapshot"},
        "days_of_stock": {"N": "1.5"},
        "current_stock": {"N": "72"},
        "avg_daily_sales": {"N": "48"},
        "correlation_id": {"S": "c1"},
        "store_id": {"S": "lima-centro"},
    }


def _healthy_inventory_image():
    img = _critical_inventory_image()
    img["days_of_stock"] = {"N": "12"}
    return img


class _LogRecorder:
    def __init__(self):
        self.events = []

    def __call__(self, level, event_type, correlation_id=None, **fields):
        self.events.append({"level": level, "event_type": event_type, **fields})

    def of_type(self, event_type):
        return [e for e in self.events if e["event_type"] == event_type]


def _patch(monkeypatch, invoke_fn):
    rec = _LogRecorder()
    monkeypatch.setattr(handler, "log", rec)
    monkeypatch.setattr(bedrock_client, "invoke", invoke_fn)
    return rec


def test_alert_generated_for_critical_stock(monkeypatch):
    calls = []

    def fake_invoke(body, **kw):
        calls.append(body)
        return "Reordenar 300 unidades hoy."

    rec = _patch(monkeypatch, fake_invoke)
    result = handler.lambda_handler(_stream_event(_critical_inventory_image()), None)

    assert result["batchItemFailures"] == []
    assert len(calls) == 1  # se invocó Bedrock una vez
    alerts = rec.of_type("alert_generated")
    assert len(alerts) == 1
    assert alerts[0]["severity"] == "critico"
    assert alerts[0]["analysis"] == "Reordenar 300 unidades hoy."
    assert alerts[0]["prompt_version"] == "v1"


def test_healthy_item_no_bedrock_no_alert(monkeypatch):
    calls = []
    rec = _patch(monkeypatch, lambda body, **kw: calls.append(body) or "x")

    result = handler.lambda_handler(_stream_event(_healthy_inventory_image()), None)

    assert result["batchItemFailures"] == []
    assert calls == []  # sin anomalía → no se llama a Bedrock (no gasta créditos)
    assert rec.of_type("alert_generated") == []


def test_bedrock_failure_is_graceful(monkeypatch):
    def boom(body, **kw):
        raise BedrockError("throttled")

    rec = _patch(monkeypatch, boom)
    result = handler.lambda_handler(_stream_event(_critical_inventory_image()), None)

    # Degradación elegante: no falla el batch (evita loops costosos), loguea el fallo.
    assert result["batchItemFailures"] == []
    assert len(rec.of_type("analysis_failed")) == 1
    assert rec.of_type("alert_generated") == []


def test_record_without_newimage_skipped(monkeypatch):
    calls = []
    _patch(monkeypatch, lambda body, **kw: calls.append(body) or "x")
    event = {"Records": [{"eventName": "REMOVE", "dynamodb": {"SequenceNumber": "9"}}]}

    result = handler.lambda_handler(event, None)

    assert result["batchItemFailures"] == []
    assert calls == []


def test_unexpected_error_reports_batch_failure(monkeypatch):
    rec = _patch(monkeypatch, lambda body, **kw: "x")
    # Forzar error inesperado en la evaluación.
    monkeypatch.setattr(handler, "evaluate", lambda item: (_ for _ in ()).throw(RuntimeError("boom")))

    result = handler.lambda_handler(_stream_event(_critical_inventory_image()), None)

    assert result["batchItemFailures"] == [{"itemIdentifier": "0"}]
    assert len(rec.of_type("processing_failed")) == 1
