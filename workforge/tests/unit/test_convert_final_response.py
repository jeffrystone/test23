from src.common.dto import ColorsEnum, Order, OrderFilterResult
from src.common.dto_msg_converters import convert_filtered_to_telegram_msg


def test_convert_filtered_shows_final_response_approve():
    o = Order(
        id="2",
        name="API",
        description="REST API",
        url="https://fl.ru/projects/2/",
        meta={
            "final_response": {
                "should_respond": True,
                "response_text": "Готов выполнить",
                "execution_days": 14,
                "price": 120000,
            },
            "order_page_scraped": True,
            "page_type": "project",
        },
    )
    fo = OrderFilterResult(order=o, telegram_message_color=ColorsEnum.green)
    msg = convert_filtered_to_telegram_msg("FL.ru", [fo])[0]
    assert "✅ Финальная LLM - Одобрить" in msg
    assert "Черновик:" in msg
    assert "Готов выполнить" in msg
    assert "14 дн." in msg
    assert "120000 ₽" in msg
    assert "order_page_scraped" not in msg


def test_convert_filtered_shows_final_response_approve_with_full_text():
    o = Order(
        id="4",
        name="API",
        description="REST API",
        url="https://fl.ru/projects/4/",
        meta={
            "final_response": {
                "should_respond": True,
                "response_text": "Готов выполнить",
                "full_text": "Добрый день!\n\nГотов выполнить\n\nПодпись",
                "execution_days": 14,
                "price": 120000,
            },
        },
    )
    fo = OrderFilterResult(order=o, telegram_message_color=ColorsEnum.green)
    msg = convert_filtered_to_telegram_msg("FL.ru", [fo])[0]
    assert "✅ Финальная LLM - Одобрить" in msg
    assert "Отклик:" in msg
    assert "Добрый день!" in msg
    assert "Подпись" in msg
    assert "Черновик:" not in msg
    assert "14 дн." in msg


def test_convert_filtered_shows_offer_result_auto_ok():
    o = Order(
        id="5",
        name="API",
        description="REST API",
        url="https://fl.ru/projects/5/",
        meta={
            "final_response": {
                "should_respond": True,
                "full_text": "Добрый день!\n\nТекст",
                "execution_days": 14,
                "price": 120000,
            },
            "offer_result": {"status": "ok"},
        },
    )
    fo = OrderFilterResult(order=o, telegram_message_color=ColorsEnum.green)
    msg = convert_filtered_to_telegram_msg("FL.ru", [fo])[0]
    assert "Auto-offer: отклик отправлен" in msg
    assert "offer_result" not in msg


def test_convert_filtered_shows_final_response_reject_skipped():
    o = Order(
        id="3",
        name="Tilda",
        description="Landing",
        url="https://fl.ru/projects/3/",
        meta={
            "final_response": {
                "should_respond": False,
                "reject_reason": "Не разработка",
            }
        },
    )
    fo = OrderFilterResult(order=o, telegram_message_color=ColorsEnum.red)
    msg = convert_filtered_to_telegram_msg(
        "FL.ru", [fo], skipped_msg=True, skipped_by_llm=True
    )[0]
    assert "❌ Финальная LLM - Отказать (Не разработка)" in msg
    assert "SEND_LLM_SKIPPED_ORDERS" in msg
