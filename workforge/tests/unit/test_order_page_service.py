import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx

from src.common.dto import Order
from src.fl.order_page_service import OrderPageService

PROJECT_HTML = """
<html>
<head><meta name="current-uid" content="12345"></head>
<body>
  <h1 class="fl-project-content__title">Full title</h1>
  <div class="fl-project-content__description-text"><p>Full description HTML</p></div>
  <div class="base-attach-class"><a href="/files/doc.pdf">doc.pdf</a></div>
  <a href="/projects/">Посмотреть другие заказы</a>
</body>
</html>
"""

GUEST_HTML = """
<html><head><meta name="current-uid" content="0"></head><body></body></html>
"""


def _make_order() -> Order:
    return Order(
        id="123",
        name="Short title",
        description="Short description",
        url="https://www.fl.ru/projects/123/test.html",
        meta={"price": "10000"},
    )


def test_enrich_order_updates_description_and_meta():
    order = _make_order()
    file_bytes = b"%PDF-1.4"

    def fake_get(url, **kwargs):
        response = MagicMock(spec=httpx.Response)
        response.raise_for_status = MagicMock()
        if url == order.url:
            response.text = PROJECT_HTML
        else:
            response.content = file_bytes
        return response

    with tempfile.TemporaryDirectory() as tmp:
        service = OrderPageService(Path(tmp))
        with patch("src.fl.order_page_service.fl_get", side_effect=fake_get):
            enriched = service.enrich_order(order, cookies={}, headers={})

        assert enriched.description == "<p>Full description HTML</p>"
        assert enriched.name == "Full title"
        assert enriched.meta["page_type"] == "project"
        assert enriched.meta["order_page_scraped"] is True
        assert enriched.meta["price"] == "10000"
        assert len(enriched.meta["files"]) == 1
        assert Path(enriched.meta["files"][0]["path"]).exists()
        assert enriched.meta["files"][0]["name"] == "doc.pdf"


def test_enrich_order_dead_session_returns_original():
    order = _make_order()

    def fake_get(url, **kwargs):
        response = MagicMock(spec=httpx.Response)
        response.raise_for_status = MagicMock()
        response.text = GUEST_HTML
        return response

    service = OrderPageService(Path("/tmp/attachments"))
    with patch("src.fl.order_page_service.fl_get", side_effect=fake_get):
        enriched = service.enrich_order(order, cookies={}, headers={})

    assert enriched is order
    assert enriched.meta.get("order_page_scraped") is None


def test_enrich_order_http_error_returns_original():
    order = _make_order()
    service = OrderPageService(Path("/tmp/attachments"))

    with patch(
        "src.fl.order_page_service.fl_get",
        side_effect=httpx.HTTPError("network"),
    ):
        enriched = service.enrich_order(order, cookies={}, headers={})

    assert enriched.description == order.description
    assert enriched.meta.get("order_page_scraped") is None


def test_enrich_orders_respects_max_count():
    orders = [
        Order(id="1", name="A", description="d", url="https://example.com/1"),
        Order(id="2", name="B", description="d", url="https://example.com/2"),
    ]

    with tempfile.TemporaryDirectory() as tmp:
        service = OrderPageService(Path(tmp))
        with patch.object(service, "enrich_order", side_effect=lambda o, **_: o) as mock:
            result = service.enrich_orders(
                orders, cookies={}, headers={}, max_count=1
            )

        assert len(result) == 1
        mock.assert_called_once()
