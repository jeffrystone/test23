from unittest.mock import MagicMock, patch

from bs4 import BeautifulSoup

from src.common.dto import ColorsEnum, Order, OrderFilterResult
from src.fl.offer_mode import OfferResult
from src.fl.offer_submitter import OfferSubmitter, order_id_from_url
from src.use_cases import FINAL_RESPONSE_META_KEY, OFFER_RESULT_META_KEY, _apply_auto_offers


def test_order_id_from_url():
    assert order_id_from_url("https://www.fl.ru/projects/5513789/foo.html") == "5513789"


def test_offer_submitter_project_ok():
    html = """
    <html><head><meta name="current-uid" content="123"></head><body>
    <input name="hash" value="abc">
    <input name="u_token_key" value="tok">
    <input name="cost_type" value="2">
    </body></html>
    """
    soup = BeautifulSoup(html, "html.parser")

    submitter = OfferSubmitter()
    with patch("src.fl.offer_submitter._fetch_page", return_value=soup), patch(
        "src.fl.offer_submitter._check_links", return_value=False
    ), patch("src.fl.offer_submitter.fl_request") as mock_request:
        mock_request.return_value = MagicMock(status_code=302, text="", headers={})
        result = submitter._submit_project(
            "https://www.fl.ru/projects/1/test.html",
            "summary",
            7,
            1000,
            {},
            soup,
            {},
        )

    assert result.status == "ok"


def test_offer_submitter_project_no_balance_without_form():
    html = """
    <html><head><meta name="current-uid" content="123"></head><body></body></html>
    """
    soup = BeautifulSoup(html, "html.parser")
    submitter = OfferSubmitter()
    result = submitter._submit_project(
        "https://www.fl.ru/projects/1/test.html",
        "summary",
        7,
        1000,
        {},
        soup,
        {},
    )
    assert result.status == "no_balance"


def test_apply_auto_offers_skipped_in_manual_mode():
    item = OrderFilterResult(
        order=Order(
            id="1",
            name="Test",
            description="Desc",
            url="https://www.fl.ru/projects/1/",
            meta={
                FINAL_RESPONSE_META_KEY: {
                    "should_respond": True,
                    "full_text": "Full text",
                    "execution_days": 5,
                    "price": 100,
                },
                "page_type": "project",
            },
        ),
        telegram_message_color=ColorsEnum.green,
    )

    with patch("src.use_cases.envs.OFFER_MODE", "manual"):
        _apply_auto_offers([item])

    assert OFFER_RESULT_META_KEY not in (item.order.meta or {})


def test_apply_auto_offers_submits_in_auto_mode():
    item = OrderFilterResult(
        order=Order(
            id="2",
            name="Test",
            description="Desc",
            url="https://www.fl.ru/projects/2/",
            meta={
                FINAL_RESPONSE_META_KEY: {
                    "should_respond": True,
                    "full_text": "Full text",
                    "execution_days": 5,
                    "price": 100,
                },
                "page_type": "project",
            },
        ),
        telegram_message_color=ColorsEnum.green,
    )

    fake_result = OfferResult(status="ok")

    with patch("src.use_cases.envs.OFFER_MODE", "auto"), patch(
        "src.use_cases.get_fl_cookies", return_value={"PHPSESSID": "x"}
    ), patch("src.use_cases.OfferSubmitter") as mock_cls:
        mock_cls.return_value.submit.return_value = fake_result
        _apply_auto_offers([item])

    assert item.order.meta[OFFER_RESULT_META_KEY]["status"] == "ok"
    mock_cls.return_value.submit.assert_called_once()
    call_kwargs = mock_cls.return_value.submit.call_args.kwargs
    assert call_kwargs["summary"] == "Full text"
    assert call_kwargs["days"] == 5
    assert call_kwargs["cost"] == 100
