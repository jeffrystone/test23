import json
from pathlib import Path
from urllib.parse import unquote

import requests

DEFAULT_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "cache-control": "max-age=0",
    "priority": "u=0, i",
    "referer": "https://www.fl.ru/projects/",
    "sec-ch-ua": '"Chromium";v="152", "Not?A_Brand";v="24", "Google Chrome";v="152"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36",
}

NO_PROXY = {"http": None, "https": None}
HTTP = requests.Session()
HTTP.trust_env = False
DEFAULT_SESSION = Path(__file__).resolve().parent / ".simulate" / "session.json"
AUTH_HINT = "нет сессии, запустите node auth.js"


def cookie_value(cookie_header, name):
    prefix = name + "="
    for part in cookie_header.split(";"):
        item = part.strip()
        if item.startswith(prefix):
            return item[len(prefix) :]
    return None


def session_cookie(session_path=None):
    path = Path(session_path) if session_path else DEFAULT_SESSION
    if not path.exists():
        raise RuntimeError(AUTH_HINT)
    data = json.loads(path.read_text(encoding="utf-8"))
    cookie = (data.get("cookie") or "").strip()
    if not cookie:
        raise RuntimeError(AUTH_HINT)
    return cookie


def xsrf_headers(cookie_header):
    token = cookie_value(cookie_header, "XSRF-TOKEN")
    if not token:
        return {}
    decoded = unquote(token)
    return {"x-xsrf-token": decoded, "x-csrf-token": decoded}


def request(url, method="GET", cookie=None, session=None, **kwargs):
    cookie = cookie or session_cookie(session)
    headers = {**DEFAULT_HEADERS, "Cookie": cookie, **kwargs.pop("headers", {})}
    kwargs.setdefault("proxies", NO_PROXY)
    return HTTP.request(method.upper(), url, headers=headers, **kwargs)
