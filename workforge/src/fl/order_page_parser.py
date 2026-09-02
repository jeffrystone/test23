import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from urllib.parse import unquote, urljoin, urlparse

from bs4 import BeautifulSoup, Tag

PageType = Literal["project", "vacancy"]

TYPE_BY_LINK_TEXT = {
    "Посмотреть другие заказы": "project",
    "Посмотреть другие вакансии": "vacancy",
}


class DeadSessionError(Exception):
    """FL.ru вернул гостевую страницу (current-uid=0)."""


@dataclass(frozen=True)
class AttachmentMeta:
    url: str
    name: str


@dataclass(frozen=True)
class OrderPageParseResult:
    page_type: PageType
    name: str
    description_html: str
    attachments: list[AttachmentMeta]


def sanitize_filename(name: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*]', "_", name).strip()
    return cleaned or "file"


def filename_for(link: Tag) -> str:
    text = link.get_text(strip=True)
    if text:
        return sanitize_filename(text)
    href = link.get("href", "")
    return sanitize_filename(unquote(Path(urlparse(href).path).name))


def parse_order_id(url: str) -> str:
    match = re.search(r"/projects/(\d+)/", url)
    return match.group(1) if match else ""


def parse_project_name(soup: BeautifulSoup) -> str:
    for selector in (
        "h1.fl-project-content__title",
        ".fl-project-content__title",
        "h1",
    ):
        node = soup.select_one(selector)
        if node:
            text = node.get_text(strip=True)
            if text:
                return text
    title = soup.find("title")
    if title:
        text = title.get_text(strip=True)
        if text:
            return text.split("|")[0].strip()
    return "Заказ"


def ensure_authenticated(soup: BeautifulSoup) -> None:
    current_uid = soup.find("meta", {"name": "current-uid"})
    if current_uid and current_uid.get("content") == "0":
        raise DeadSessionError("FL.ru session is dead (current-uid=0)")


def detect_page_type(soup: BeautifulSoup) -> PageType:
    found: list[PageType] = []
    for link in soup.find_all("a"):
        page_type = TYPE_BY_LINK_TEXT.get(link.get_text(strip=True))
        if page_type and page_type not in found:
            found.append(page_type)
    if len(found) == 1:
        return found[0]
    if not found:
        raise RuntimeError(
            "Не найден тип страницы: нет ссылки «Посмотреть другие заказы» "
            "или «Посмотреть другие вакансии»"
        )
    raise RuntimeError(
        "Неоднозначный тип страницы: найдены ссылки и на заказы, и на вакансии"
    )


def parse_attachments(soup: BeautifulSoup, base_url: str) -> list[AttachmentMeta]:
    files: list[AttachmentMeta] = []
    seen: set[str] = set()
    for attach in soup.select(".base-attach-class"):
        for link in attach.select("a[href]"):
            url = urljoin(base_url, link["href"])
            if url in seen:
                continue
            seen.add(url)
            files.append(AttachmentMeta(url=url, name=filename_for(link)))
    return files


def parse_order_page_html(html: str, base_url: str) -> OrderPageParseResult:
    soup = BeautifulSoup(html, "html.parser")
    ensure_authenticated(soup)
    page_type = detect_page_type(soup)
    description = soup.select_one(".fl-project-content__description-text")
    description_html = description.decode_contents() if description else ""
    name = parse_project_name(soup)
    attachments = parse_attachments(soup, base_url)
    return OrderPageParseResult(
        page_type=page_type,
        name=name,
        description_html=description_html,
        attachments=attachments,
    )
