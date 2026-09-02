from src.common.cookies import merge_cookies


def test_merge_cookies_keeps_stored_session():
    stored = {
        "PHPSESSID": "abc123",
        "XSRF-TOKEN": "token",
        "id": "1",
    }
    updated = {
        "__ddg10_": "1788217018",
        "__ddg8_": "e8twPDL6u9XB6l27",
    }
    merged = merge_cookies(stored, updated)
    assert merged["PHPSESSID"] == "abc123"
    assert merged["XSRF-TOKEN"] == "token"
    assert merged["__ddg10_"] == "1788217018"


def test_merge_cookies_overwrites_updated_keys():
    stored = {"XSRF-TOKEN": "old"}
    updated = {"XSRF-TOKEN": "new"}
    merged = merge_cookies(stored, updated)
    assert merged["XSRF-TOKEN"] == "new"
