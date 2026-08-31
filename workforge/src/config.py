from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent


class Envs(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DEBUG: bool = True
    DB_PATH: Path = BASE_DIR / "app.db"

    SEND_SKIPPED_ORDERS: bool = True
    SEND_LLM_SKIPPED_ORDERS: bool = True

    SEND_DEBUG_INFO: bool = True
    ENABLE_CLASSIFICATION: bool = True

    # Без дефолтов: приложение должно падать на старте, если секрет не задан,
    # а не молча уходить в работу со значением из репозитория.
    OPENAI_KEY: str
    DEFAULT_OPENAI_MODEL: str = "gpt-5-mini"
    POLLING_INTERVAL: int = 1800  # in seconds
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_CHANNEL_ID: str = ""

    # Anthropic (фаза 2–3; ключ опционален, пока API не используем)
    ANTHROPIC_API_KEY: str = ""
    DEFAULT_ANTHROPIC_MODEL: str = "claude-sonnet-4-5-20250929"
    ANTHROPIC_MAX_TOKENS: int = 64

    ENABLE_FINAL_LLM: bool = False
    FINAL_LLM_MAX_ORDERS: int = 1
    FINAL_LLM_MAX_TOKENS: int = 512
    ORDER_ATTACHMENTS_DIR: Path = BASE_DIR.parent / "staticfiles" / "fl" / "attachments"

