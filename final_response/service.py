import asyncio
import json
import logging

from final_response.config import FinalResponseEnvs
from final_response.prompts import load_response_prompt
from final_response.provider import LLMProvider, get_provider
from final_response.schemas import FinalResponseResult, LLMResponsePayload, OrderInput

logger = logging.getLogger(__name__)


async def evaluate_order(
    order: OrderInput,
    *,
    provider: LLMProvider | None = None,
    envs: FinalResponseEnvs | None = None,
) -> FinalResponseResult:
    envs = envs or FinalResponseEnvs()
    provider = provider or get_provider(envs)

    system_prompt = load_response_prompt()
    user_payload = order.model_dump_json(exclude_none=True)

    raw = await provider.generate_json(
        system=system_prompt,
        user=user_payload,
        max_tokens=envs.AI_MAX_TOKENS,
    )

    payload = LLMResponsePayload.model_validate(json.loads(raw))
    result = FinalResponseResult.from_llm_payload(order.id, payload)
    logger.info(
        "Final response for order %s: should_respond=%s",
        order.id,
        result.should_respond,
    )
    return result


def evaluate_order_sync(
    order: OrderInput,
    *,
    provider: LLMProvider | None = None,
    envs: FinalResponseEnvs | None = None,
) -> FinalResponseResult:
    return asyncio.run(
        evaluate_order(order, provider=provider, envs=envs),
    )
