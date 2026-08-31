import json
import os

import httpx

from src.common.utils import save_json


def load_cookies_from_file(p) -> dict:
    p = p + "/cookies.json"
    if not os.path.exists(p):
        return {}

    with open(p, "r", encoding="utf-8") as file:
        return json.load(file)


def fetch_cookies(base_url, headers, cookies=None):
    response = httpx.get(
        base_url, headers=headers, follow_redirects=True, cookies=cookies
    )
    cookies = response.cookies
    return dict(cookies)


def load_cookies(base_url, headers, cookies_dir):
    current_cookies = load_cookies_from_file(cookies_dir)
    fetched_cookies = fetch_cookies(base_url, headers, current_cookies)
    save_json(fetched_cookies, cookies_dir, "cookies")
    return fetched_cookies
