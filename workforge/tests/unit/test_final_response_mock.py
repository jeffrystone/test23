import asyncio
import json

from src.final_response.providers.mock import APPROVE_PAYLOAD, REJECT_PAYLOAD, MockProvider
from src.final_response.schemas import LLMResponsePayload


async def _run_mock(system: str, user: str, provider: MockProvider | None = None):
    provider = provider or MockProvider()
    return await provider.generate_json(system=system, user=user, max_tokens=64)


def test_mock_provider_returns_approve_by_default():
    raw = asyncio.run(_run_mock("sys", '{"name": "Разработка API"}'))
    payload = LLMResponsePayload.model_validate(json.loads(raw))
    assert payload.should_respond is True
    assert payload.response_text
    assert payload.execution_days == APPROVE_PAYLOAD["execution_days"]
    assert payload.price == APPROVE_PAYLOAD["price"]


def test_mock_provider_returns_reject_when_keyword_present():
    provider = MockProvider(reject_if_contains="отказ")
    raw = asyncio.run(
        _run_mock("sys", '{"description": "нужен отказ от проекта"}', provider=provider)
    )
    payload = LLMResponsePayload.model_validate(json.loads(raw))
    assert payload.should_respond is False
    assert payload.reject_reason == REJECT_PAYLOAD["reject_reason"]
