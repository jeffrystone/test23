import json
import logging
import os

import httpx

from src.common.fl_http import fl_get
from src.common.utils import save_json

logger = logging.getLogger(__name__)


def load_cookies_from_file(p) -> dict:
    p = p + "/cookies.json"
    if not os.path.exists(p):
        return {}

    with open(p, "r", encoding="utf-8") as file:
        return json.load(file)


def merge_cookies(stored: dict, updated: dict) -> dict:
    merged = dict(stored)
    merged.update(updated)
    return merged


def fetch_cookies(base_url, headers, cookies=None):
    response = fl_get(
        base_url, headers=headers, cookies=cookies or {}
    )
    return dict(response.cookies)


def load_cookies(base_url, headers, cookies_dir):
    current_cookies = load_cookies_from_file(cookies_dir)
    try:
        updated_cookies = fetch_cookies(base_url, headers, current_cookies)
        merged_cookies = merge_cookies(current_cookies, updated_cookies)
    except httpx.HTTPError as exc:
        logger.warning("Failed to refresh FL.ru cookies, using stored: %s", exc)
        merged_cookies = current_cookies

    if merged_cookies:
        save_json(merged_cookies, cookies_dir, "cookies")
    return merged_cookies
