from typing import Protocol

from final_response.config import FinalResponseEnvs


class LLMProvider(Protocol):
    async def generate_json(self, *, system: str, user: str, max_tokens: int) -> str: ...


def get_provider(envs: FinalResponseEnvs | None = None) -> LLMProvider:
    envs = envs or FinalResponseEnvs()
    provider_name = envs.AI_MODE.strip().lower()

    if provider_name == "yandex":
        from final_response.providers.yandex import YandexProvider

        return YandexProvider(envs)

    if provider_name == "claude":
        from final_response.providers.claude import ClaudeProvider

        return ClaudeProvider(envs)

    from final_response.providers.mock import MockProvider

    return MockProvider()
