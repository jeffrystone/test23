from src.fl.offer_mode import (
    is_auto_offer,
    is_manual_offer,
    normalize_offer_mode,
)


def test_normalize_offer_mode_defaults_to_manual():
    assert normalize_offer_mode(None) == "manual"
    assert normalize_offer_mode("manual") == "manual"
    assert normalize_offer_mode("AUTO") == "auto"


def test_is_manual_and_auto_offer():
    assert is_manual_offer("manual") is True
    assert is_auto_offer("manual") is False
    assert is_auto_offer("auto") is True
    assert is_manual_offer("auto") is False
