import logging

from openai import AsyncOpenAI

from final_response.config import FinalResponseEnvs

logger = logging.getLogger(__name__)

YANDEX_BASE_URL = "https://llm.api.cloud.yandex.net/v1"


class YandexProvider:
    """Yandex Cloud Foundation Models через OpenAI-compatible API."""

    def __init__(self, envs: FinalResponseEnvs):
        if not envs.YANDEX_API_KEY or not envs.YANDEX_FOLDER_ID:
            raise ValueError(
                "YANDEX_API_KEY and YANDEX_FOLDER_ID are required for yandex provider"
            )
        self._model = f"gpt://{envs.YANDEX_FOLDER_ID}/{envs.YANDEX_MODEL}"
        self._client = AsyncOpenAI(
            api_key=envs.YANDEX_API_KEY,
            base_url=YANDEX_BASE_URL,
        )
        logger.info("YandexProvider initialized with model=%s", self._model)

    async def generate_json(self, *, system: str, user: str, max_tokens: int) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or ""
        usage = getattr(response, "usage", None)
        if usage:
            logger.info(
                "Yandex usage: prompt=%s completion=%s total=%s",
                getattr(usage, "prompt_tokens", None),
                getattr(usage, "completion_tokens", None),
                getattr(usage, "total_tokens", None),
            )
        logger.debug("Yandex raw response: %s", content)
        return content
