import pytest

from src.common.dto import Order, OrderFilterResult, ColorsEnum
from src.common.dto_msg_converters import convert_filtered_to_telegram_msg

expected_message = """Платформа: FL.ru

📝 Название: Москва
📄 Описание: Уважаемый [Имя дистрибьютора]!  Мы были бы рады предложить Вам долгосрочное сотрудничество в рамках дистрибуции нашей продукции. Наша компания стремится к расширению...
💰 Стоимость: по договоренности
🕒 11 минут назад
💬 Сколько откликов: Нет ответов
🔗 Ссылка:  https://fl.ru/projects/5494227/moskva.html
Дополнительно:
   • views: 11

🟡 Позитивные/Негативные/Стоп: 0/0/0

"""




@pytest.mark.parametrize(
    "expected_postfix, llm_classification, filter_with_llm",
    (
        [
            """❌ LLM фильтрация - Отказать (Коммерческое предложение о дистрибуции, не относится к разработке ПО.)""",
            {
                "approved": False,
                "reason": "Коммерческое предложение о дистрибуции, не относится к разработке ПО."
            },
            True,
        ],

        [
            """✅ LLM фильтрация - Одобрить (Коммерческое предложение о дистрибуции, не относится к разработке ПО.)""",
            {
                "approved": True,
                "reason": "Коммерческое предложение о дистрибуции, не относится к разработке ПО."
            },
            True
        ],

        [
            """⚪ LLM фильтрация - Не делалась""",
            {},
            True
        ],

        [
            """⚪ LLM фильтрация - Не делалась""",
            None,
            False
        ],
    )

)
def test_convert_filtered_to_telegram_msg(expected_postfix, llm_classification, filter_with_llm) -> None:

    o = Order(
        id="1",
        name="Москва",
        description="Уважаемый [Имя дистрибьютора]!  Мы были бы рады предложить Вам долгосрочное сотрудничество в рамках дистрибуции нашей продукции. Наша компания стремится к расширению...",
        url="https://fl.ru/projects/5494227/moskva.html",
        meta={
            "price": 'по договоренности',
            "answers": "Нет ответов",
            "time_posted": "11 минут назад",
            "views": 11,
            "llm_classification": llm_classification
        }
    )
    fo = OrderFilterResult(
            order=o,
            count_positive_keywords=0,
            count_negative_keywords=0,
            count_stop_keywords=0,
            send_to_telegram=False,
            filter_with_llm=filter_with_llm,
            telegram_message_color=ColorsEnum.yellow,
        )

    result_messages = convert_filtered_to_telegram_msg(
        platform='FL.ru',
        data=[fo],
        skipped_msg=False
    )
    assert result_messages[0] == expected_message + expected_postfix