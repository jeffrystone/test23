import logging

from anthropic import AsyncAnthropic

from final_response.config import FinalResponseEnvs

logger = logging.getLogger(__name__)


class ClaudeProvider:
    """Anthropic Claude через нативный SDK."""

    def __init__(self, envs: FinalResponseEnvs):
        if not envs.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is required for claude provider")
        self._model = envs.ANTHROPIC_MODEL
        self._client = AsyncAnthropic(api_key=envs.ANTHROPIC_API_KEY)
        logger.info("ClaudeProvider initialized with model=%s", self._model)

    async def generate_json(self, *, system: str, user: str, max_tokens: int) -> str:
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        content = "".join(block.text for block in response.content if block.type == "text")
        logger.info(
            "Claude usage: input=%s output=%s",
            response.usage.input_tokens,
            response.usage.output_tokens,
        )
        logger.debug("Claude raw response: %s", content)
        return content.strip()
