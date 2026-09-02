import logging
import re
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from src.common.fl_http import fl_request
from src.fl.offer_mode import OfferResult, xsrf_headers

logger = logging.getLogger(__name__)

ORDER_ID_RE = re.compile(r"/projects/(\d+)/")


def order_id_from_url(url: str) -> str:
    match = ORDER_ID_RE.search(urlparse(url).path)
    if not match:
        raise RuntimeError(f"Не удалось взять id заказа из URL: {url}")
    return match.group(1)


def _field_value(soup, name: str) -> str | None:
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


def _token_key(soup) -> str | None:
    value = _field_value(soup, "u_token_key")
    if value:
        return value
    meta = soup.find("meta", {"name": "_TOKEN_KEY"})
    if meta and meta.get("content"):
        return meta["content"]
    return None


def _has_links_from(response) -> int:
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


def _html_snippet(text: str, limit: int = 400) -> str:
    return " ".join(text.split())[:limit]


def _already_offered_project(soup) -> bool:
    return soup.find(attrs={"data-function": "document.openChat"}) is not None


def _already_offered_vacancy(soup) -> bool:
    tag = soup.find("vacancy-offer")
    if tag is None:
        return False
    for key in ("is-my-offer", ":is-my-offer"):
        if (tag.get(key) or "").lower() == "true":
            return True
    return False


def _is_resume_required(soup) -> bool:
    tag = soup.find("vacancy-offer")
    if tag is None:
        return False
    for key in ("is-resume-required", ":is-resume-required"):
        value = (tag.get(key) or "").lower()
        if value in ("true", "1"):
            return True
    return False


def _uid_from_html(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    meta = soup.find("meta", {"name": "current-uid"})
    if meta and meta.get("content") is not None:
        return meta.get("content").strip()
    return None


def _fetch_page(url: str, cookies: dict, headers: dict) -> BeautifulSoup:
    response = fl_request("GET", url, cookies=cookies, headers={**headers, "referer": url})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    current_uid = soup.find("meta", {"name": "current-uid"})
    if current_uid and current_uid.get("content") == "0":
        raise RuntimeError("сессия мертвая, обновите cookies FL.ru")
    return soup


def _json_api_headers(cookies: dict, referer: str, soup) -> dict:
    api_headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "origin": "https://www.fl.ru",
        "referer": referer,
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        **xsrf_headers(cookies),
    }
    csrf_meta = soup.find("meta", {"name": "csrf-token"})
    if csrf_meta and csrf_meta.get("content"):
        api_headers["x-csrf-token"] = csrf_meta["content"]
    return api_headers


def _upload_resume(
    resume_path: str,
    cookies: dict,
    target: str,
    soup,
    headers: dict,
) -> str:
    path = Path(resume_path)
    if not path.is_file():
        raise RuntimeError(f"Файл резюме не найден: {resume_path}")

    api_headers = _json_api_headers(cookies, target, soup)
    session = fl_request(
        "POST",
        "https://www.fl.ru/storage/upload/session/",
        cookies=cookies,
        headers={**headers, **api_headers},
        json={"type": "offer_resume"},
    )
    if session.status_code in (401, 403, 419):
        raise RuntimeError("сессия мертвая, обновите cookies FL.ru")
    if session.status_code >= 400:
        raise RuntimeError(
            f"upload session HTTP {session.status_code}: {_html_snippet(session.text)}"
        )
    session_id = session.json().get("session_id")
    if not session_id:
        raise RuntimeError("upload session: нет session_id в ответе")

    upload_headers = {
        "accept": "application/json",
        "origin": "https://www.fl.ru",
        "referer": target,
        "File-Session": session_id,
        **xsrf_headers(cookies),
    }
    csrf_meta = soup.find("meta", {"name": "csrf-token"})
    if csrf_meta and csrf_meta.get("content"):
        upload_headers["x-csrf-token"] = csrf_meta["content"]

    with path.open("rb") as handle:
        upload = fl_request(
            "POST",
            "https://www.fl.ru/storage/upload/",
            cookies=cookies,
            headers={**headers, **upload_headers},
            files={"files[]": (path.name, handle, "application/octet-stream")},
        )
    if upload.status_code in (401, 403, 419):
        raise RuntimeError("сессия мертвая, обновите cookies FL.ru")
    if upload.status_code >= 400:
        raise RuntimeError(
            f"upload file HTTP {upload.status_code}: {_html_snippet(upload.text)}"
        )
    payload = upload.json()
    file_session_id = payload.get("session_id") or session_id
    if not payload.get("items"):
        raise RuntimeError("upload file: сервер не принял файл")
    return file_session_id


def _check_links(
    order_id_value: str,
    summary: str,
    cookies: dict,
    target: str,
    soup,
    headers: dict,
) -> bool:
    check = fl_request(
        "POST",
        f"https://www.fl.ru/projects/{order_id_value}/offers/check-links/",
        cookies=cookies,
        headers={**headers, **_json_api_headers(cookies, target, soup)},
        json={"description": summary},
    )
    if check.status_code in (401, 403, 419):
        raise RuntimeError("сессия мертвая, обновите cookies FL.ru")
    if check.status_code >= 400:
        raise RuntimeError(
            f"check-links HTTP {check.status_code}: {_html_snippet(check.text)}"
        )
    return bool(_has_links_from(check))


class OfferSubmitter:
    def submit(
        self,
        *,
        url: str,
        summary: str,
        days: int,
        cost: int,
        page_type: str,
        cookies: dict,
        headers: dict,
        resume_path: str | None = None,
    ) -> OfferResult:
        soup = _fetch_page(url, cookies, headers)
        if page_type == "vacancy":
            return self._submit_vacancy(
                url, summary, cookies, soup, headers, resume_path=resume_path
            )
        return self._submit_project(url, summary, days, cost, cookies, soup, headers)

    def _submit_project(
        self,
        target: str,
        summary: str,
        days: int,
        cost: int,
        cookies: dict,
        soup,
        headers: dict,
    ) -> OfferResult:
        order_id_value = order_id_from_url(target)

        if _already_offered_project(soup):
            return OfferResult(status="already")

        hash_value = _field_value(soup, "hash")
        token = _token_key(soup)
        if not hash_value or not token:
            return OfferResult(status="no_balance")

        cost_type = _field_value(soup, "cost_type") or "2"
        links = _check_links(order_id_value, summary, cookies, target, soup, headers)

        form = {
            "descr": summary,
            "has_links": str(int(links)),
            "time_from": str(days),
            "cost_from": str(cost),
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
        submit = fl_request(
            "POST",
            target,
            cookies=cookies,
            headers={
                **headers,
                "content-type": "application/x-www-form-urlencoded",
                "origin": "https://www.fl.ru",
                "referer": target,
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "same-origin",
                "sec-fetch-user": "?1",
            },
            data=form,
            follow_redirects=False,
        )
        if submit.status_code in (301, 302, 303):
            logger.info(
                "Offer submitted for %s: HTTP %s",
                target,
                submit.status_code,
            )
            return OfferResult(status="ok")
        if submit.status_code in (401, 403, 419):
            raise RuntimeError("сессия мертвая, обновите cookies FL.ru")
        if submit.status_code == 200:
            uid = _uid_from_html(submit.text)
            if uid and uid != "0":
                return OfferResult(status="no_balance")
        raise RuntimeError(
            f"Отклик не принят: HTTP {submit.status_code} {_html_snippet(submit.text)}"
        )

    def _submit_vacancy(
        self,
        target: str,
        summary: str,
        cookies: dict,
        soup,
        headers: dict,
        *,
        resume_path: str | None = None,
        file_session_id: str = "",
    ) -> OfferResult:
        order_id_value = order_id_from_url(target)

        if _already_offered_vacancy(soup):
            return OfferResult(status="already")

        resume_required = _is_resume_required(soup)
        if resume_path:
            file_session_id = _upload_resume(resume_path, cookies, target, soup, headers)
        elif resume_required and not file_session_id:
            raise RuntimeError(
                "Вакансия требует резюме: укажите FL_RESUME_PATH в .env"
            )

        has_links = _check_links(order_id_value, summary, cookies, target, soup, headers)
        payload = {
            "description": summary,
            "file_session_id": file_session_id,
            "has_links": has_links,
            "remove_resume": 0 if file_session_id else 1,
        }
        submit = fl_request(
            "POST",
            f"https://www.fl.ru/vacancy/{order_id_value}/offers/",
            cookies=cookies,
            headers={**headers, **_json_api_headers(cookies, target, soup)},
            json=payload,
        )
        if submit.status_code in (401, 403, 419):
            raise RuntimeError("сессия мертвая, обновите cookies FL.ru")
        if submit.status_code == 201:
            return OfferResult(status="ok")
        if submit.status_code in (400, 409) and "already" in submit.text.lower():
            return OfferResult(status="already")
        if submit.status_code == 402 or "no_balance" in submit.text.lower():
            return OfferResult(status="no_balance")
        raise RuntimeError(
            f"Отклик не принят: HTTP {submit.status_code} {_html_snippet(submit.text)}"
        )
