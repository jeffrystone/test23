import asyncio

from src.final_response.config import FinalResponseEnvs
from src.final_response.provider import get_provider
from src.final_response.providers.mock import MockProvider
from src.final_response.schemas import OrderInput
from src.final_response.service import evaluate_order


def test_evaluate_order_with_mock_provider():
    sample_order = OrderInput(
        id="12345",
        name="Разработка backend на Python",
        description="Нужен REST API, интеграция с PostgreSQL, деплой на VPS.",
        url="https://www.fl.ru/projects/12345/",
    )
    envs = FinalResponseEnvs(FINAL_RESPONSE_PROVIDER="mock")
    provider = get_provider(envs)
    assert isinstance(provider, MockProvider)

    result = asyncio.run(
        evaluate_order(sample_order, provider=provider, envs=envs)
    )

    assert result.order_id == "12345"
    assert result.should_respond is True
    assert result.response_text
    assert result.execution_days is not None
    assert result.price is not None
    assert result.reject_reason is None


def test_evaluate_order_reject_scenario():
    order = OrderInput(
        id="999",
        name="Tilda лендинг",
        description="Нужен отказ — перенос landing page на Tilda",
    )
    envs = FinalResponseEnvs(FINAL_RESPONSE_PROVIDER="mock")
    result = asyncio.run(
        evaluate_order(order, provider=get_provider(envs), envs=envs)
    )

    assert result.order_id == "999"
    assert result.should_respond is False
    assert result.reject_reason
