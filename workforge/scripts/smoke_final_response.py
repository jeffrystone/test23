#!/usr/bin/env python3
"""Smoke-test для модуля final_response (mock или yandex)."""

import json
import logging
import sys

from src.final_response.config import FinalResponseEnvs
from src.final_response.schemas import OrderInput
from src.final_response.service import evaluate_order_sync

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("smoke_final_response")


SAMPLE_ORDER = OrderInput(
    id="smoke-1",
    name="Разработка Telegram-бота на Python",
    description=(
        "Нужен бот для приёма заявок, интеграция с Google Sheets, "
        "админ-панель на FastAPI. Срок обсуждаем."
    ),
    url="https://www.fl.ru/projects/smoke-1/",
)


def main() -> int:
    envs = FinalResponseEnvs()
    provider_name = envs.FINAL_RESPONSE_PROVIDER.strip().lower()
    logger.info("Provider: %s", provider_name)

    if provider_name == "yandex":
        if not envs.YANDEX_API_KEY or not envs.YANDEX_FOLDER_ID:
            logger.error("Set YANDEX_API_KEY and YANDEX_FOLDER_ID in src/.env")
            return 1

    try:
        result = evaluate_order_sync(SAMPLE_ORDER, envs=envs)
    except Exception as exc:
        logger.exception("evaluate_order failed: %s", exc)
        return 1

    print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
