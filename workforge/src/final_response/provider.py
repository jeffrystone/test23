from typing import Protocol

from src.final_response.config import FinalResponseEnvs


class LLMProvider(Protocol):
    async def generate_json(self, *, system: str, user: str, max_tokens: int) -> str: ...


def get_provider(envs: FinalResponseEnvs | None = None) -> LLMProvider:
    from src.final_response.providers.mock import MockProvider
    from src.final_response.providers.yandex import YandexProvider

    envs = envs or FinalResponseEnvs()
    provider_name = envs.FINAL_RESPONSE_PROVIDER.strip().lower()

    if provider_name == "yandex":
        return YandexProvider(envs)

    return MockProvider()
