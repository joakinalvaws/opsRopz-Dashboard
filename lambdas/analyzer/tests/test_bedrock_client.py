import io
import json
import os
import sys

import pytest
from botocore.exceptions import ClientError

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bedrock_client  # noqa: E402
from bedrock_client import BedrockError, invoke  # noqa: E402


def _response(text):
    payload = {"content": [{"type": "text", "text": text}]}
    return {"body": io.BytesIO(json.dumps(payload).encode())}


def _client_error(code):
    return ClientError({"Error": {"Code": code, "Message": "x"}}, "InvokeModel")


class FakeClient:
    """Cliente Bedrock falso: encola respuestas o excepciones por llamada."""

    def __init__(self, behaviors):
        self.behaviors = list(behaviors)
        self.calls = 0

    def invoke_model(self, **kwargs):
        b = self.behaviors[self.calls]
        self.calls += 1
        if isinstance(b, Exception):
            raise b
        return b


def test_success_returns_text():
    client = FakeClient([_response("Reordenar 300 unidades hoy.")])
    out = invoke({"messages": []}, client=client, sleep=lambda s: None)
    assert out == "Reordenar 300 unidades hoy."
    assert client.calls == 1


def test_retries_on_throttling_then_succeeds():
    sleeps = []
    client = FakeClient([_client_error("ThrottlingException"), _response("ok")])
    out = invoke({"messages": []}, client=client, sleep=sleeps.append)
    assert out == "ok"
    assert client.calls == 2
    assert sleeps == [1]  # primer backoff = 2**0 = 1s


def test_exponential_backoff_sequence():
    sleeps = []
    client = FakeClient(
        [_client_error("ThrottlingException"), _client_error("ServiceUnavailableException"), _response("ok")]
    )
    out = invoke({"messages": []}, client=client, sleep=sleeps.append, max_attempts=3)
    assert out == "ok"
    assert sleeps == [1, 2]  # 2**0, 2**1


def test_non_retryable_raises_immediately():
    client = FakeClient([_client_error("AccessDeniedException")])
    with pytest.raises(BedrockError):
        invoke({"messages": []}, client=client, sleep=lambda s: None)
    assert client.calls == 1  # no reintenta


def test_exhausts_retries_raises():
    client = FakeClient([_client_error("ThrottlingException")] * 3)
    with pytest.raises(BedrockError):
        invoke({"messages": []}, client=client, sleep=lambda s: None, max_attempts=3)
    assert client.calls == 3
