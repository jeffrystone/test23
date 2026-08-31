import json
import logging

logger = logging.getLogger(__name__)

APPROVE_PAYLOAD = {
    "should_respond": True,
    "response_text": "Готов взяться за задачу. Имею опыт разработки похожих решений и могу предложить архитектуру под ваши требования.",
    "execution_days": 14,
    "price": 120000,
    "reject_reason": None,
}

REJECT_PAYLOAD = {
    "should_respond": False,
    "response_text": None,
    "execution_days": None,
    "price": None,
    "reject_reason": "Заказ не соответствует профилю команды.",
}


class MockProvider:
    """LLM-заглушка для unit-тестов и локальной разработки без API."""

    def __init__(self, reject_if_contains: str = "отказ"):
        self.reject_if_contains = reject_if_contains.lower()

    async def generate_json(self, *, system: str, user: str, max_tokens: int) -> str:
        payload = REJECT_PAYLOAD if self.reject_if_contains in user.lower() else APPROVE_PAYLOAD
        logger.info("MockProvider response for payload size=%d chars", len(user))
        return json.dumps(payload, ensure_ascii=False)
