from datetime import datetime
from typing import Any, Iterable


from src.common.dto import Order, OrderFilterResult, OrderList, ColorsEnum, RunStats


def _format_meta_item(key: str, value: Any) -> str:
    return f"{key}: {value}"

def _format_llm_meta(data: dict | None, filter_with_llm: bool = True) -> str:
    template = "{icon} LLM фильтрация - {resolution}"
    resolution, icon, description = None, None, None

    if not filter_with_llm or not data:
        resolution = "Не делалась"
        icon = "⚪"
    else:
        template +=  " ({description})"

    if data:
        description = data.get("reason")
        if data.get("approved"):
            resolution = "Одобрить"
            icon = "✅"
        else:
            resolution = "Отказать"
            icon = "❌"
    return template.format(icon=icon, resolution=resolution, description=description)


def _format_final_response_meta(data: dict | None) -> str:
    if not data:
        return "⚪ Финальная LLM - Не делалась"

    if data.get("should_respond"):
        full_text = data.get("full_text")
        if full_text:
            indented = "\n".join(f"   {line}" for line in full_text.splitlines())
            body_line = f"   Отклик:\n{indented}"
        else:
            body_line = f"   Черновик: {data.get('response_text') or '—'}"
        lines = [
            "✅ Финальная LLM - Одобрить",
            body_line,
            f"   Срок: {data.get('execution_days')} дн.",
            f"   Цена: {data.get('price')} ₽",
        ]
        return "\n".join(lines)

    reason = data.get("reject_reason") or "без причины"
    return f"❌ Финальная LLM - Отказать ({reason})"


ENRICHMENT_META_KEYS = ("order_page_scraped", "page_type", "files")



def _build_order_message(
    platform: str,
    now: str,
    order: Order,
    extra_lines: Iterable[str] | None = None,
) -> str:

    order.meta = order.meta or {}
    answers = order.meta.pop("answers", None)
    time_posted = order.meta.pop("time_posted", None)
    price = order.meta.pop("price", None)

    order.meta.pop("qa_project_name", None)
    order.meta.pop("data_id", None)
    order.meta.pop("image_urls", None)
    for key in ENRICHMENT_META_KEYS:
        order.meta.pop(key, None)

    lines = [
        f"Платформа: {platform}",
        "",
        f"📝 Название: {order.name}",
        f"📄 Описание: {order.description}",
        f"💰 Стоимость: {price}",
        f"🕒 {time_posted}",
        f"💬 Сколько откликов: {answers}",
        f"🔗 Ссылка:  {order.url}",
    ]

    if order.meta:
        meta_lines = [f"   • {_format_meta_item(k, v)}" for k, v in order.meta.items()]
        lines.append("Дополнительно:\n" + "\n".join(meta_lines))

    if extra_lines:
        lines.extend(extra_lines)

    return "\n".join(lines)


def convert_to_telegram_msg(platform: str, data: "OrderList") -> list[str]:
    if not data.orders:
        return []

    now = datetime.now().isoformat()

    return [_build_order_message(platform, now, order) for order in data.orders]


def color_to_symbol(color: ColorsEnum) -> str:
    symbols = {
        ColorsEnum.green: "✅",
        ColorsEnum.red: "❌",
        ColorsEnum.yellow: "🟡",
        ColorsEnum.notset: "⚪",
    }

    if isinstance(color, ColorsEnum):
        return symbols.get(color, "⚪")

    try:
        return symbols.get(ColorsEnum(color), "⚪")
    except (ValueError, TypeError):
        return "⚪"


def convert_filtered_to_telegram_msg(
    platform: str, data: list[OrderFilterResult] | Any, skipped_msg: bool | None = None, skipped_by_llm: bool | None = None
) -> list[str]:

    filtered_orders = data.orders if hasattr(data, "orders") else data
    if not filtered_orders:
        return []

    now = datetime.now().isoformat()
    messages = []
    for item in filtered_orders:
        llm_meta = item.order.meta.pop("llm_classification", None)
        final_response_meta = item.order.meta.pop("final_response", None)

        symbol = color_to_symbol(item.telegram_message_color)
        extra_lines = [
            "",
            f"{symbol} Позитивные/Негативные/Стоп: {item.count_positive_keywords}/{item.count_negative_keywords}/{item.count_stop_keywords}",
            "",
            _format_llm_meta(llm_meta, item.filter_with_llm),
            _format_final_response_meta(final_response_meta),
        ]

        if skipped_msg:
            env_name = "SEND_LLM_SKIPPED_ORDERS" if skipped_by_llm else "SEND_SKIPPED_ORDERS"

            extra_lines.extend(
                [
                    "",
                    "",
                    "skipped.",
                    f"*this message will not appear if you disable the {env_name} in env*",
                ]
            )
        messages.append(
            _build_order_message(platform, now, item.order, extra_lines=extra_lines)
        )
    return messages


def run_stats_to_msg(stat: RunStats) -> str:
    timestamp = stat.start_at.isoformat()
    skipped_count = len(stat.skipped_orders or [])
    skipped_by_llm_count = len(stat.skipped_by_llm or [])
    exceptions = getattr(stat, "exceptions", None) or getattr(stat, "exception", None)

    lines = [
        "📊 [DEV] Статистика запуска",

        "",
        f"🆕 Новых заказов: {stat.new_orders}",
        f"🚫 Скипнуто по правилам: {skipped_count}",
        f"🤖 Отправлено в LLM: {stat.llm_requests}",
        f"🧠 Скипнуто LLM: {skipped_by_llm_count}",
        f"📨 Отправлено в Telegram: {stat.telegram_sent}",
    ]

    if exceptions:
        lines.append(f"❗ Ошибки: {exceptions}")
    else:
        lines.append("✅ Ошибок нет")

    lines.extend(
        [
            "",
            "",
            "*this message will not appear if you disable the SEND_DEBUG_INFO in env*",
        ]
    )
    return "\n".join(lines)
