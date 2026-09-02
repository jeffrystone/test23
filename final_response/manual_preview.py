import argparse
import json
from pathlib import Path


def format_manual_preview(order_url: str, order_response: dict) -> str:
    summary = (order_response.get("summary") or "").strip() or "—"
    days = order_response.get("days")
    cost = order_response.get("estimate_cost")

    lines = [
        "Manual review — отклик не отправлен на FL",
        "",
        f"Ссылка: {order_url}",
        "",
        summary,
        "",
        f"Срок: {days if days is not None else '—'} дн.",
        f"Стоимость: {cost if cost is not None else '—'} руб.",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Manual review preview for stand pipeline")
    parser.add_argument("--url", required=True, help="URL заказа на FL.ru")
    parser.add_argument("--order-response", required=True, help="Путь к order-response.json")
    args = parser.parse_args()

    order_response = json.loads(Path(args.order_response).read_text(encoding="utf-8"))
    print(format_manual_preview(args.url, order_response))


if __name__ == "__main__":
    main()
