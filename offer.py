import argparse
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from requester import request, session_cookie, xsrf_headers

ORDER_ID_RE = re.compile(r"/projects/(\d+)/")


def order_id(url):
    match = ORDER_ID_RE.search(urlparse(url).path)
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


def already_offered_project(soup):
    return soup.find(attrs={"data-function": "document.openChat"}) is not None


def already_offered_vacancy(soup):
    tag = soup.find("vacancy-offer")
    if tag is None:
        return False
    for key in ("is-my-offer", ":is-my-offer"):
        if (tag.get(key) or "").lower() == "true":
            return True
    return False


def is_resume_required(soup):
    tag = soup.find("vacancy-offer")
    if tag is None:
        return False
    for key in ("is-resume-required", ":is-resume-required"):
        value = (tag.get(key) or "").lower()
        if value in ("true", "1"):
            return True
    return False


def uid_from_html(html):
    soup = BeautifulSoup(html, "html.parser")
    meta = soup.find("meta", {"name": "current-uid"})
    if meta and meta.get("content") is not None:
        return meta.get("content").strip()
    return None


def fetch_page(target, cookie):
    page = request(target, cookie=cookie, headers={"referer": target})
    page.raise_for_status()
    soup = BeautifulSoup(page.text, "html.parser")
    current_uid = soup.find("meta", {"name": "current-uid"})
    if current_uid and current_uid.get("content") == "0":
        raise RuntimeError("сессия мертвая, запустите node auth.js")
    return page, soup


def json_api_headers(cookie, referer, soup):
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "origin": "https://www.fl.ru",
        "referer": referer,
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        **xsrf_headers(cookie),
    }
    csrf_meta = soup.find("meta", {"name": "csrf-token"})
    if csrf_meta and csrf_meta.get("content"):
        headers["x-csrf-token"] = csrf_meta["content"]
    return headers


def upload_resume(resume_path, cookie, target, soup):
    path = Path(resume_path)
    if not path.is_file():
        raise RuntimeError(f"Файл резюме не найден: {resume_path}")

    headers = json_api_headers(cookie, target, soup)
    session = request(
        "https://www.fl.ru/storage/upload/session/",
        method="POST",
        cookie=cookie,
        headers=headers,
        json={"type": "offer_resume"},
    )
    if session.status_code in (401, 403, 419):
        raise RuntimeError("сессия мертвая, запустите node auth.js")
    if session.status_code >= 400:
        raise RuntimeError(
            f"upload session HTTP {session.status_code}: {html_snippet(session.text)}"
        )
    session_id = session.json().get("session_id")
    if not session_id:
        raise RuntimeError("upload session: нет session_id в ответе")

    upload_headers = {
        "accept": "application/json",
        "origin": "https://www.fl.ru",
        "referer": target,
        "File-Session": session_id,
        **xsrf_headers(cookie),
    }
    csrf_meta = soup.find("meta", {"name": "csrf-token"})
    if csrf_meta and csrf_meta.get("content"):
        upload_headers["x-csrf-token"] = csrf_meta["content"]

    with path.open("rb") as handle:
        upload = request(
            "https://www.fl.ru/storage/upload/",
            method="POST",
            cookie=cookie,
            headers=upload_headers,
            files={"files[]": (path.name, handle, "application/octet-stream")},
        )
    if upload.status_code in (401, 403, 419):
        raise RuntimeError("сессия мертвая, запустите node auth.js")
    if upload.status_code >= 400:
        raise RuntimeError(
            f"upload file HTTP {upload.status_code}: {html_snippet(upload.text)}"
        )
    payload = upload.json()
    file_session_id = payload.get("session_id") or session_id
    if not payload.get("items"):
        raise RuntimeError("upload file: сервер не принял файл")
    return file_session_id


def check_links(order_id_value, summary, cookie, target, soup):
    check = request(
        f"https://www.fl.ru/projects/{order_id_value}/offers/check-links/",
        method="POST",
        cookie=cookie,
        headers=json_api_headers(cookie, target, soup),
        json={"description": summary},
    )
    if check.status_code in (401, 403, 419):
        raise RuntimeError("сессия мертвая, запустите node auth.js")
    if check.status_code >= 400:
        raise RuntimeError(
            f"check-links HTTP {check.status_code}: {html_snippet(check.text)}"
        )
    return bool(has_links_from(check))


def submit_project(target, order, cookie, soup):
    order_id_value = order_id(target)
    summary = order["summary"]

    if already_offered_project(soup):
        print("offer: already")
        sys.exit(0)

    hash_value = field_value(soup, "hash")
    token = token_key(soup)
    if not hash_value or not token:
        print("offer: no_balance")
        sys.exit(2)
    cost_type = field_value(soup, "cost_type") or "2"
    links = check_links(order_id_value, summary, cookie, target, soup)

    form = {
        "descr": summary,
        "has_links": str(int(links)),
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
    if submit.status_code in (301, 302, 303):
        print(f"status: {submit.status_code}")
        print(f"location: {submit.headers.get('Location', '')}")
        print("offer: ok")
        return
    if submit.status_code in (401, 403, 419):
        raise RuntimeError("сессия мертвая, запустите node auth.js")
    if submit.status_code == 200:
        uid = uid_from_html(submit.text)
        if uid and uid != "0":
            print("offer: no_balance")
            sys.exit(2)
    raise RuntimeError(
        f"Отклик не принят: HTTP {submit.status_code} {html_snippet(submit.text)}"
    )


def submit_vacancy(target, order, cookie, soup, file_session_id="", resume_path=None):
    order_id_value = order_id(target)
    summary = order["summary"]

    if already_offered_vacancy(soup):
        print("offer: already")
        sys.exit(0)

    resume_required = is_resume_required(soup)
    if resume_path:
        file_session_id = upload_resume(resume_path, cookie, target, soup)
    elif resume_required and not file_session_id:
        raise RuntimeError(
            "Вакансия требует резюме: укажите FL_RESUME_PATH в .env "
            "или --resume-path"
        )

    has_links = check_links(order_id_value, summary, cookie, target, soup)
    payload = {
        "description": summary,
        "file_session_id": file_session_id,
        "has_links": has_links,
        "remove_resume": 0 if file_session_id else 1,
    }
    submit = request(
        f"https://www.fl.ru/vacancy/{order_id_value}/offers/",
        method="POST",
        cookie=cookie,
        headers=json_api_headers(cookie, target, soup),
        json=payload,
    )
    if submit.status_code in (401, 403, 419):
        raise RuntimeError("сессия мертвая, запустите node auth.js")
    if submit.status_code == 201:
        print(f"status: {submit.status_code}")
        print("offer: ok")
        return
    if submit.status_code in (400, 409) and "already" in submit.text.lower():
        print("offer: already")
        sys.exit(0)
    if submit.status_code == 402 or "no_balance" in submit.text.lower():
        print("offer: no_balance")
        sys.exit(2)
    raise RuntimeError(
        f"Отклик не принят: HTTP {submit.status_code} {html_snippet(submit.text)}"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    parser.add_argument("--order-response", required=True)
    parser.add_argument("--session", required=True)
    parser.add_argument(
        "--type",
        choices=["project", "vacancy"],
        required=True,
        help="тип страницы FL.ru",
    )
    parser.add_argument(
        "--file-session-id",
        default="",
        help="готовый file_session_id (если файл уже загружен вручную)",
    )
    parser.add_argument(
        "--resume-path",
        default=os.environ.get("FL_RESUME_PATH", ""),
        help="путь к файлу резюме (.pdf, .doc, …); env FL_RESUME_PATH",
    )
    args = parser.parse_args()

    order = json.loads(Path(args.order_response).read_text(encoding="utf-8"))
    cookie = session_cookie(args.session)
    target = args.target

    _, soup = fetch_page(target, cookie)

    if args.type == "vacancy":
        resume_path = args.resume_path.strip() or None
        file_session_id = args.file_session_id.strip()
        submit_vacancy(
            target,
            order,
            cookie,
            soup,
            file_session_id=file_session_id,
            resume_path=resume_path,
        )
    else:
        submit_project(target, order, cookie, soup)


if __name__ == "__main__":
    main()
