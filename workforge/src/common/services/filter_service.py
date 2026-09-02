import logging

from src.common.keyword_counter import AbstractKeywordCounter
from src.common.dto import Order, OrderFilterResult, ColorsEnum

logger = logging.getLogger("filter_service")


class FilterService:
    def __init__(
        self,
        positive_keyword_counter: AbstractKeywordCounter,
        negative_keyword_counter: AbstractKeywordCounter,
        stop_keyword_counter: AbstractKeywordCounter,
    ):
        self.positive_keyword_counter = positive_keyword_counter
        self.negative_keyword_counter = negative_keyword_counter
        self.stop_keyword_counter = stop_keyword_counter

    def _get_keyword_counts(self, order: Order) -> tuple[int, int, int]:
        text = f"{order.name}\n{order.description}"
        positive = self.positive_keyword_counter.count_keywords(text)
        negative = self.negative_keyword_counter.count_keywords(text)
        stop = self.stop_keyword_counter.count_keywords(text)
        logger.info(
            "Positive: %d. Negative: %d. Stop: %d. Text: '%s'", positive.count_kw, negative.count_kw, stop.count_kw, text,
            extra={"positive": positive, "negative": negative, "stop": stop},
        )
        return positive.count_kw, negative.count_kw, stop.count_kw

    def _calculate_color(self, positive: int, negative: int, stop: int) -> ColorsEnum:
        if stop > 0:
            return ColorsEnum.red
        if positive == negative or negative > positive > 0:
            return ColorsEnum.yellow
        if positive > 0:
            return ColorsEnum.green
        if negative > 0:
            return ColorsEnum.red
        return ColorsEnum.yellow

    def _can_send_without_llm(
        self, positive: int, negative: int, stop: int
    ) -> bool | None:
        """
        У этого метода есть три возможных выход

         Если true сразу отправляем
         Если None, не решили ещё, нужно в llm
         Если False, не отправляем вовсе
        """
        if (stop > 0) or (positive == 0 and negative >= 2):
            # 1 и более стоп слов: не отправляем никуда
            # или
            # 2 и более негативных-слов и нет положительных триггеров: не отправляем никуда
            return False

        return None


    def _should_filter_with_llm(self, positive: int, negative: int) -> bool:
        return positive >= 1 and positive >= negative

    def filter(self, order: Order) -> OrderFilterResult:
        # TODO: cюда order уже должны прийти с обогащенными данными
        pos_count, neg_count, stop_count = self._get_keyword_counts(order)
        send_telegram = self._can_send_without_llm(pos_count, neg_count, stop_count)
        should_llm_filtering = False

        if send_telegram is None:
            should_llm_filtering = True

        return OrderFilterResult(
            order=order,
            count_negative_keywords=neg_count,
            count_positive_keywords=pos_count,
            count_stop_keywords=stop_count,
            send_to_telegram=(
                True if send_telegram else False
            ),  # поскольку значение может быть неопределённое None ставим False
            filter_with_llm=should_llm_filtering,
            telegram_message_color=self._calculate_color(pos_count, neg_count, stop_count),
        )
