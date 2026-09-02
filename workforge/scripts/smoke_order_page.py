"""Smoke: парсинг страницы заказа FL.ru вне process_fl."""

import argparse
import sys
from pathlib import Path

# repo root on PYTHONPATH when run as: PYTHONPATH=. python scripts/smoke_order_page.py
from src.common import consts
from src.common.dto import Order
from src.config import Envs
from src.fl.main import get_fl_cookies
from src.fl.order_page_service import OrderPageService


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke order page scrape")
    parser.add_argument("--target", required=True, help="URL страницы заказа FL.ru")
    args = parser.parse_args()

    envs = Envs()
    service = OrderPageService(envs.ORDER_ATTACHMENTS_DIR)
    order = Order(
        id="smoke",
        name="",
        description="",
        url=args.target,
    )

    enriched = service.enrich_order(
        order,
        cookies=get_fl_cookies(),
        headers=consts.HEADERS,
    )

    if not enriched.meta or not enriched.meta.get("order_page_scraped"):
        print("FAIL: order page was not scraped (check session/cookies)", file=sys.stderr)
        return 1

    files = enriched.meta.get("files") or []
    preview = enriched.description[:200].replace("\n", " ")
    print(f"page_type: {enriched.meta.get('page_type')}")
    print(f"name: {enriched.name}")
    print(f"files: {len(files)}")
    print(f"description_preview: {preview}")
    for item in files:
        print(f"  - {item.get('name')} -> {item.get('path')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
