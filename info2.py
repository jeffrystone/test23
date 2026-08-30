import argparse
import json
import re
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

from bs4 import BeautifulSoup

from requester import request, session_cookie


def sanitize_filename(name):
    cleaned = re.sub(r'[<>:"/\\|?*]', "_", name).strip()
    return cleaned or "file"


def filename_for(link):
    text = link.get_text(strip=True)
    if text:
        return sanitize_filename(text)
    return sanitize_filename(unquote(Path(urlparse(link["href"]).path).name))


def unique_path(directory, filename):
    path = directory / filename
    if not path.exists():
        return path
    stem, suffix = path.stem, path.suffix
    index = 2
    while True:
        candidate = directory / f"{stem}_{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


TYPE_BY_LINK_TEXT = {
    "Посмотреть другие заказы": "project",
    "Посмотреть другие вакансии": "vacancy",
}


def detect_type(soup):
    found = []
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


def parse_project(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    page_type = detect_type(soup)
    description = soup.select_one(".fl-project-content__description-text")
    summary = description.decode_contents() if description else ""

    files = []
    seen = set()
    for attach in soup.select(".base-attach-class"):
        for link in attach.select("a[href]"):
            url = urljoin(base_url, link["href"])
            if url in seen:
                continue
            seen.add(url)
            files.append({"url": url, "name": filename_for(link)})
    return page_type, summary, files


def download_files(entries, output_dir, cookie):
    output_dir.mkdir(parents=True, exist_ok=True)
    result = []
    for entry in entries:
        dest = unique_path(output_dir, entry["name"])
        response = request(entry["url"], cookie=cookie)
        response.raise_for_status()
        dest.write_bytes(response.content)
        result.append({"url": entry["url"], "path": str(dest)})
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, help="URL заказа")
    parser.add_argument("--output", required=True, help="путь к JSON")
    parser.add_argument("--output-dir", required=True, help="каталог для вложений")
    parser.add_argument("--session", help="путь к session.json")
    args = parser.parse_args()

    cookie = session_cookie(args.session)
    response = request(args.target, cookie=cookie)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    current_uid = soup.find("meta", {"name": "current-uid"})
    if current_uid and current_uid.get("content") == "0":
        raise RuntimeError("сессия мертвая, запустите node auth.js")
    page_type, summary, parsed_files = parse_project(response.text, args.target)
    files = download_files(parsed_files, Path(args.output_dir), cookie)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps({"type": page_type, "summary": summary, "files": files}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"status: {response.status_code}")
    print(f"type: {page_type}")
    print(f"files: {len(files)}")
    print(f"json: {output}")


if __name__ == "__main__":
    main()
