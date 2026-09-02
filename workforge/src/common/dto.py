from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel


class Order(BaseModel):
    id: str
    name: str
    description: str
    url: str
    meta: Optional[dict[str, Any]] = None


class OrderList(BaseModel):
    orders: list[Order]


class ColorsEnum(str, Enum):
    yellow = "yellow"
    red = "red"
    green = "green"
    notset = "notset"


@dataclass
class OrderFilterResult:
    order: Order
    count_negative_keywords: int = 0
    count_positive_keywords: int = 0
    count_stop_keywords: int = 0
    send_to_telegram: bool = True
    filter_with_llm: bool = True
    telegram_message_color: ColorsEnum = ColorsEnum.notset

@dataclass
class RunStats:
    start_at: datetime
    new_orders: int = 0 # сколько всего новых заказов
    telegram_sent: int = 0 # сколько уведомлений было отправлено в телеграм,
    llm_requests: int = 0 # сколько было запросов в ллм,
    not_sent: int = 0 # сколько заказов не отправлено.
    skipped_orders: list = field(default_factory=list) # cкипнутые заказы
    skipped_by_llm: list = field(default_factory=list) # cкипнутые заказы с помощью llm
    exceptions: Any | None = None # ошибки во время выполнения итерации
