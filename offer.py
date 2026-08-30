import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from requester import request, session_cookie, xsrf_headers

PROJECT_ID_RE = re.compile(r"/projects/(\d+)/")


def project_id(url):
    match = PROJECT_ID_RE.search(urlparse(url).path)
    if not match:
        raise RuntimeError(f"Не удалось взять id заказа из URL: {url}")
    return match.group(1)


def field_value(soup, name):
    element = soup.find("input", {"name": name})
    if element is not None and element.get("value") is not None:
        return element.get("value")
    select = soup.find("select", {"name": name})
    if select is not None:
        selected = select.find("option", selected=True) or select.find("option")
        if selected is not None and selected.get("value") is not None:
            return selected.get("value")
    textarea = soup.find("textarea", {"name": name})
    if textarea is not None:
        return textarea.get_text()
    return None


def token_key(soup):
    value = field_value(soup, "u_token_key")
    if value:
        return value
    meta = soup.find("meta", {"name": "_TOKEN_KEY"})
    if meta and meta.get("content"):
        return meta["content"]
    return None


def has_links_from(response):
    try:
        payload = response.json()
    except ValueError:
        return 0
    if isinstance(payload, dict):
        if "has_links" in payload:
            return int(payload["has_links"] or 0)
        data = payload.get("data")
        if isinstance(data, dict) and "has_links" in data:
            return int(data["has_links"] or 0)
    return 0


def html_snippet(text, limit=400):
    return " ".join(text.split())[:limit]


def already_offered(soup):
    return soup.find(attrs={"data-function": "document.openChat"}) is not None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    parser.add_argument("--order-response", required=True)
    parser.add_argument("--session", required=True)
    args = parser.parse_args()

    order = json.loads(Path(args.order_response).read_text(encoding="utf-8"))
    cookie = session_cookie(args.session)
    target = args.target
    order_id = project_id(target)
    summary = order["summary"]

    page = request(target, cookie=cookie, headers={"referer": target})
    page.raise_for_status()
    soup = BeautifulSoup(page.text, "html.parser")
    current_uid = soup.find("meta", {"name": "current-uid"})
    if current_uid and current_uid.get("content") == "0":
        raise RuntimeError("сессия мертвая, запустите node auth.js")

    if already_offered(soup):
        print("offer: already")
        sys.exit(0)

    hash_value = field_value(soup, "hash")
    token = token_key(soup)
    if not hash_value or not token:
        raise RuntimeError(
            "На странице нет hash/u_token_key — сессия или форма отклика недоступны. "
            f"{html_snippet(page.text)}"
        )
    cost_type = field_value(soup, "cost_type") or "2"

    check_headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "origin": "https://www.fl.ru",
        "referer": target,
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        **xsrf_headers(cookie),
    }
    csrf_meta = soup.find("meta", {"name": "csrf-token"})
    if csrf_meta and csrf_meta.get("content"):
        check_headers["x-csrf-token"] = csrf_meta["content"]

    check = request(
        f"https://www.fl.ru/projects/{order_id}/offers/check-links/",
        method="POST",
        cookie=cookie,
        headers=check_headers,
        json={"description": summary},
    )
    if check.status_code in (401, 403, 419):
        raise RuntimeError("сессия мертвая, запустите node auth.js")
    if check.status_code >= 400:
        raise RuntimeError(
            f"check-links HTTP {check.status_code}: {html_snippet(check.text)}"
        )
    links = has_links_from(check)

    form = {
        "descr": summary,
        "has_links": str(links),
        "time_from": str(order["days"]),
        "cost_from": str(order["estimate_cost"]),
        "cost_type": str(cost_type),
        "portf_id1": "",
        "portf_id2": "",
        "portf_id3": "",
        "pict1": "",
        "pict2": "",
        "pict3": "",
        "prev_pict1": "",
        "prev_pict2": "",
        "prev_pict3": "",
        "calc": "0",
        "hash": hash_value,
        "submit": "",
        "u_token_key": token,
    }
    submit = request(
        target,
        method="POST",
        cookie=cookie,
        headers={
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://www.fl.ru",
            "referer": target,
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
        },
        data=form,
        allow_redirects=False,
    )
    if submit.status_code not in (301, 302, 303):
        raise RuntimeError(
            f"Отклик не принят: HTTP {submit.status_code} {html_snippet(submit.text)}"
        )

    print(f"status: {submit.status_code}")
    print(f"location: {submit.headers.get('Location', '')}")
    print("offer: ok")


if __name__ == "__main__":
    main()
