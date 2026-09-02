from src.common.utils import get_keywords


def test_get_keywords_reads_keywords_from_file(tmp_path):
    keywords_content = [
        "кабинет",
        "подписк",
        "## коментарий",
        "-- коментарий 2",
        "",
        "",
        "тариф",
        "договор",
        "платеж",
        "эквайринг",
        "счет",
        "регистрац",
        "авторизац",
        "вход по",
    ]
    expected_keywords = [
        "кабинет",
        "подписк",
        "тариф",
        "договор",
        "платеж",
        "эквайринг",
        "счет",
        "регистрац",
        "авторизац",
        "вход по",
    ]
    keywords_file = tmp_path / "keywords.txt"
    keywords_file.write_text("\n".join(keywords_content))

    result = get_keywords(keywords_file)

    assert result == expected_keywords
