from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from final_response.assemble import assemble_response
from final_response.greeting import get_time_greeting
from final_response.signature import load_signature

MSK = timezone(timedelta(hours=3))


def _msk(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 9, 1, hour, minute, tzinfo=MSK)


@pytest.mark.parametrize(
    ("hour", "expected"),
    [
        (5, "Доброе утро!"),
        (11, "Доброе утро!"),
        (12, "Добрый день!"),
        (17, "Добрый день!"),
        (18, "Добрый вечер!"),
        (4, "Добрый вечер!"),
        (0, "Добрый вечер!"),
    ],
)
def test_get_time_greeting_msk_boundaries(hour: int, expected: str):
    assert get_time_greeting(now=_msk(hour)) == expected


def test_get_time_greeting_boundary_minutes():
    assert get_time_greeting(now=_msk(11, 59)) == "Доброе утро!"
    assert get_time_greeting(now=_msk(12, 0)) == "Добрый день!"
    assert get_time_greeting(now=_msk(17, 59)) == "Добрый день!"
    assert get_time_greeting(now=_msk(18, 0)) == "Добрый вечер!"


def test_load_signature_reads_file(tmp_path: Path):
    signature_file = tmp_path / "signature.txt"
    signature_file.write_text("  Подпись\n", encoding="utf-8")

    assert load_signature(signature_file) == "Подпись"


def test_load_signature_missing_file(tmp_path: Path):
    missing = tmp_path / "missing.txt"
    with pytest.raises(FileNotFoundError, match="Signature file not found"):
        load_signature(missing)


def test_load_signature_empty_file(tmp_path: Path):
    empty = tmp_path / "empty.txt"
    empty.write_text("   \n", encoding="utf-8")
    with pytest.raises(ValueError, match="Signature file is empty"):
        load_signature(empty)


def test_assemble_response_joins_parts(tmp_path: Path):
    signature_file = tmp_path / "signature.txt"
    signature_file.write_text("С уважением,\nАвтор", encoding="utf-8")

    result = assemble_response(
        "Текст отклика от LLM.",
        now=_msk(10),
        signature_path=signature_file,
    )

    assert result == "Доброе утро!\n\nТекст отклика от LLM.\n\nС уважением,\nАвтор"


def test_assemble_response_empty_llm_text(tmp_path: Path):
    signature_file = tmp_path / "signature.txt"
    signature_file.write_text("Подпись", encoding="utf-8")

    result = assemble_response(
        "",
        now=_msk(14),
        signature_path=signature_file,
    )

    assert result == "Добрый день!\n\nПодпись"
