from datetime import timezone, datetime

from src.common.dto import RunStats


class CollectStatService:
    def __init__(self) -> None:
        self.stats: RunStats = RunStats(datetime.now(timezone.utc))

    def add_llm_requests_count(self, count):
        self.stats.llm_requests += count

    def get_actual_stats(self) -> RunStats:
        return self.stats

    def add_skipped(self, orders: list, by_llm):
        if by_llm:
            self.stats.skipped_by_llm.extend(orders)
        else:
            self.stats.skipped_orders.extend(orders)
        self.stats.not_sent += len(orders)

    def save_new_orders_count(self, orders: list):
        self.stats.new_orders += len(orders)

    def add_count_send(self, orders):
        self.stats.telegram_sent += len(orders)

    def register_exception(self, exc: BaseException) -> None:
        self.stats.exceptions = exc