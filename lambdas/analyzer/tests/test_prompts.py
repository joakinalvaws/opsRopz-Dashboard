import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prompts import (  # noqa: E402
    PROMPT_VERSION,
    SYSTEM_PROMPT,
    build_bedrock_body,
    build_user_prompt,
)

_ITEM = {
    "sku": "LECHE_GLORIA_1L",
    "store_id": "lima-centro",
    "current_stock": 72,
    "avg_daily_sales": 48.0,
    "days_of_stock": 1.5,
}


class TestUserPrompt:
    def test_includes_context(self):
        p = build_user_prompt(_ITEM, "Stock para 1.5 días")
        assert "LECHE_GLORIA_1L" in p
        assert "lima-centro" in p
        assert "1.5" in p
        assert "Stock para 1.5 días" in p

    def test_omits_missing_fields(self):
        p = build_user_prompt({"sku": "X"}, "algo")
        assert "Stock actual" not in p
        assert "X" in p


class TestBedrockBody:
    def test_messages_api_shape(self):
        body = build_bedrock_body(_ITEM, "Stock crítico")
        assert body["anthropic_version"] == "bedrock-2023-05-31"
        assert body["system"] == SYSTEM_PROMPT
        assert body["messages"][0]["role"] == "user"
        assert "max_tokens" in body

    def test_respects_max_tokens(self):
        body = build_bedrock_body(_ITEM, "x", max_tokens=123)
        assert body["max_tokens"] == 123


def test_prompt_version_pinned():
    assert PROMPT_VERSION == "v1"
