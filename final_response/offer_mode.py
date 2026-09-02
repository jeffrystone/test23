from final_response.config import FinalResponseEnvs

DEFAULT_OFFER_MODE = "manual"
VALID_OFFER_MODES = frozenset({"manual", "auto"})


def normalize_offer_mode(mode: str | None) -> str:
    value = (mode or DEFAULT_OFFER_MODE).strip().lower()
    if value not in VALID_OFFER_MODES:
        raise ValueError(
            f"Invalid OFFER_MODE: {mode!r}. Expected one of: {', '.join(sorted(VALID_OFFER_MODES))}"
        )
    return value


def is_auto_offer(mode: str | None = None) -> bool:
    resolved = normalize_offer_mode(mode if mode is not None else FinalResponseEnvs().OFFER_MODE)
    return resolved == "auto"


def is_manual_offer(mode: str | None = None) -> bool:
    return not is_auto_offer(mode)
