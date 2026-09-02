import logging
from pathlib import Path

from src.common.fl_http import fl_get
from src.common.dto import Order
from src.fl.order_page_parser import (
    AttachmentMeta,
    DeadSessionError,
    OrderPageParseResult,
    parse_order_page_html,
    sanitize_filename,
)

logger = logging.getLogger(__name__)


def unique_path(directory: Path, filename: str) -> Path:
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


class OrderPageService:
    def __init__(self, attachments_dir: Path):
        self._attachments_dir = attachments_dir

    def enrich_orders(
        self,
        orders: list[Order],
        *,
        cookies: dict,
        headers: dict,
        max_count: int,
    ) -> list[Order]:
        enriched: list[Order] = []
        for order in orders[:max_count]:
            enriched.append(
                self.enrich_order(order, cookies=cookies, headers=headers)
            )
        return enriched

    def enrich_order(
        self,
        order: Order,
        *,
        cookies: dict,
        headers: dict,
    ) -> Order:
        try:
            parsed, downloaded = self._fetch_and_parse(order, cookies, headers)
        except DeadSessionError:
            logger.warning("Dead FL.ru session while scraping order %s", order.id)
            return order
        except Exception as exc:
            logger.warning(
                "Failed to scrape order page %s: %s",
                order.id,
                exc,
                exc_info=True,
            )
            return order

        meta = dict(order.meta or {})
        meta["page_type"] = parsed.page_type
        meta["files"] = downloaded
        meta["order_page_scraped"] = True

        return order.model_copy(
            update={
                "name": parsed.name or order.name,
                "description": parsed.description_html or order.description,
                "meta": meta,
            }
        )

    def _fetch_and_parse(
        self,
        order: Order,
        cookies: dict,
        headers: dict,
    ) -> tuple[OrderPageParseResult, list[dict[str, str]]]:
        response = fl_get(
            order.url,
            headers=headers,
            cookies=cookies,
            timeout=30.0,
        )
        response.raise_for_status()
        parsed = parse_order_page_html(response.text, order.url)
        downloaded = self._download_attachments(
            parsed.attachments,
            order.id,
            cookies=cookies,
            headers=headers,
        )
        return parsed, downloaded

    def _download_attachments(
        self,
        attachments: list[AttachmentMeta],
        order_id: str,
        *,
        cookies: dict,
        headers: dict,
    ) -> list[dict[str, str]]:
        if not attachments:
            return []

        output_dir = self._attachments_dir / order_id
        output_dir.mkdir(parents=True, exist_ok=True)
        result: list[dict[str, str]] = []

        for entry in attachments:
            filename = sanitize_filename(entry.name)
            dest = unique_path(output_dir, filename)
            file_response = fl_get(
                entry.url,
                headers=headers,
                cookies=cookies,
                timeout=60.0,
            )
            file_response.raise_for_status()
            dest.write_bytes(file_response.content)
            result.append(
                {
                    "url": entry.url,
                    "name": filename,
                    "path": str(dest),
                }
            )
        return result
