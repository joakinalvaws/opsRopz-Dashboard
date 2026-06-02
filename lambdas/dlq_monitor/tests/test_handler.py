import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import handler


class _FakeSQS:
    def __init__(self, count: int):
        self._count = count

    def get_queue_attributes(self, **kw):
        return {"Attributes": {"ApproximateNumberOfMessages": str(self._count)}}


class _FakeSNS:
    def __init__(self):
        self.published: list = []

    def publish(self, **kw):
        self.published.append(kw)


def _setup(monkeypatch, count: int):
    sns = _FakeSNS()
    monkeypatch.setattr(handler, "_sqs_client", _FakeSQS(count))
    monkeypatch.setattr(handler, "_sns_client", sns)
    monkeypatch.setattr(handler, "_DLQ_URL", "https://sqs.us-east-1.amazonaws.com/123/dlq")
    monkeypatch.setattr(handler, "_SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123:test")
    return sns


def test_empty_dlq_returns_zero_without_sns(monkeypatch):
    sns = _setup(monkeypatch, 0)

    result = handler.lambda_handler({}, None)

    assert result == {"dlq_messages": 0}
    assert sns.published == []


def test_messages_in_dlq_publishes_to_sns(monkeypatch):
    sns = _setup(monkeypatch, 3)

    result = handler.lambda_handler({}, None)

    assert result == {"dlq_messages": 3}
    assert len(sns.published) == 1
    assert "CRITICO" in sns.published[0]["Subject"]
    assert "3" in sns.published[0]["Subject"]


def test_sns_message_contains_count(monkeypatch):
    import json

    sns = _setup(monkeypatch, 5)

    handler.lambda_handler({}, None)

    msg = json.loads(sns.published[0]["Message"])
    assert msg["dlq_count"] == 5
    assert msg["severity"] == "critico"
    assert msg["rule"] == "mensajes_en_dlq"


def test_subject_truncated_to_100_chars(monkeypatch):
    sns = _setup(monkeypatch, 999)

    handler.lambda_handler({}, None)

    assert len(sns.published[0]["Subject"]) <= 100
