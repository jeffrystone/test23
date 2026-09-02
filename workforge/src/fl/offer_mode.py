from enum import Enum
from pathlib import Path
from urllib.parse import unquote, urlparse

from pydantic import BaseModel

DEFAULT_OFFER_MODE = "manual"
VALID_OFFER_MODES = frozenset({"manual", "auto"})


class OfferMode(str, Enum):
    manual = "manual"
    auto = "auto"


def normalize_offer_mode(mode: str | None) -> str:
    value = (mode or DEFAULT_OFFER_MODE).strip().lower()
    if value not in VALID_OFFER_MODES:
        raise ValueError(
            f"Invalid OFFER_MODE: {mode!r}. Expected one of: {', '.join(sorted(VALID_OFFER_MODES))}"
        )
    return value


def is_auto_offer(mode: str | None) -> bool:
    return normalize_offer_mode(mode) == OfferMode.auto.value


def is_manual_offer(mode: str | None) -> bool:
    return not is_auto_offer(mode)


class OfferResult(BaseModel):
    status: str
    message: str | None = None


def xsrf_headers(cookies: dict) -> dict:
    token = cookies.get("XSRF-TOKEN")
    if not token:
        return {}
    decoded = unquote(token)
    return {"x-xsrf-token": decoded, "x-csrf-token": decoded}
