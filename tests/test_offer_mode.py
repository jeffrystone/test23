import pytest

from final_response.manual_preview import format_manual_preview
from final_response.offer_mode import (
    DEFAULT_OFFER_MODE,
    is_auto_offer,
    is_manual_offer,
    normalize_offer_mode,
)


def test_normalize_offer_mode_defaults_to_manual():
    assert normalize_offer_mode(None) == "manual"
    assert normalize_offer_mode("") == "manual"
    assert DEFAULT_OFFER_MODE == "manual"


def test_normalize_offer_mode_accepts_auto_and_manual():
    assert normalize_offer_mode("auto") == "auto"
    assert normalize_offer_mode("MANUAL") == "manual"
    assert normalize_offer_mode(" Auto ") == "auto"


def test_normalize_offer_mode_rejects_invalid():
    with pytest.raises(ValueError, match="Invalid OFFER_MODE"):
        normalize_offer_mode("invalid")


def test_is_auto_offer_and_manual_offer():
    assert is_manual_offer("manual") is True
    assert is_auto_offer("manual") is False
    assert is_manual_offer("auto") is False
    assert is_auto_offer("auto") is True


def test_format_manual_preview_includes_url_summary_days_cost():
    order_response = {
        "summary": "Добрый день!\n\nГотов выполнить задачу.",
        "days": 14,
        "estimate_cost": 120000,
    }
    text = format_manual_preview("https://www.fl.ru/projects/123/", order_response)

    assert "Manual review" in text
    assert "https://www.fl.ru/projects/123/" in text
    assert "Готов выполнить задачу." in text
    assert "14 дн." in text
    assert "120000 руб." in text


def test_format_manual_preview_handles_missing_fields():
    text = format_manual_preview("https://example.com", {})

    assert "https://example.com" in text
    assert "—" in text
