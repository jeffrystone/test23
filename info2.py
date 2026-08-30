import argparse
import json
import re
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

from bs4 import BeautifulSoup

from requester import request


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


def parse_order_id(url):
    match = re.search(r"/projects/(\d+)/", url)
    return match.group(1) if match else ""


def parse_project_name(soup):
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


def parse_project(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    description = soup.select_one(".fl-project-content__description-text")
    summary = description.decode_contents() if description else ""
    name = parse_project_name(soup)

    files = []
    seen = set()
    for attach in soup.select(".base-attach-class"):
        for link in attach.select("a[href]"):
            url = urljoin(base_url, link["href"])
            if url in seen:
                continue
            seen.add(url)
            files.append({"url": url, "name": filename_for(link)})
    return name, summary, files


def download_files(entries, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    result = []
    for entry in entries:
        dest = unique_path(output_dir, entry["name"])
        response = request(entry["url"])
        response.raise_for_status()
        dest.write_bytes(response.content)
        result.append({"url": entry["url"], "path": str(dest)})
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, help="URL заказа")
    parser.add_argument("--output", required=True, help="путь к JSON")
    parser.add_argument("--output-dir", required=True, help="каталог для вложений")
    args = parser.parse_args()

    response = request(args.target)
    response.raise_for_status()
    name, summary, parsed_files = parse_project(response.text, args.target)
    files = download_files(parsed_files, Path(args.output_dir))

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "id": parse_order_id(args.target),
                "url": args.target,
                "name": name,
                "summary": summary,
                "files": files,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"status: {response.status_code}")
    print(f"files: {len(files)}")
    print(f"json: {output}")


if __name__ == "__main__":
    main()
