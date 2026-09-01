from unittest.mock import patch

from src.common.dto import ColorsEnum, Order, OrderFilterResult
from src.common.services.collect_stat_service import CollectStatService
from src.final_response.schemas import FinalResponseResult
from src.use_cases import (
    FINAL_RESPONSE_META_KEY,
    _apply_final_llm_filtering,
    order_to_final_response_input,
)


def _make_filter_result(
    order_id: str,
    description: str = "Нужен backend на Python",
) -> OrderFilterResult:
    return OrderFilterResult(
        order=Order(
            id=order_id,
            name="Test order",
            description=description,
            url=f"https://www.fl.ru/projects/{order_id}/",
        ),
        telegram_message_color=ColorsEnum.green,
    )


def test_order_to_final_response_input_passes_meta():
    order = Order(
        id="1",
        name="Title",
        description="Desc",
        url="https://example.com",
        meta={"page_type": "project", "files": []},
    )
    result = order_to_final_response_input(order)
    assert result.id == "1"
    assert result.meta == {"page_type": "project", "files": []}


def test_apply_final_llm_approve():
    stat = CollectStatService()
    items = [_make_filter_result("101")]

    async def fake_evaluate(order, envs=None):
        return FinalResponseResult(
            order_id="101",
            should_respond=True,
            response_text="Черновик",
            execution_days=10,
            price=50000,
        )

    with patch("src.use_cases.envs.ENABLE_FINAL_LLM", True), patch(
        "src.use_cases.envs.FINAL_LLM_MAX_ORDERS", 1
    ), patch("src.use_cases.evaluate_order", side_effect=fake_evaluate):
        approved, rejected_ids, skipped = _apply_final_llm_filtering(items, stat)

    assert len(approved) == 1
    assert not rejected_ids
    assert not skipped
    meta = approved[0].order.meta[FINAL_RESPONSE_META_KEY]
    assert meta["should_respond"] is True
    assert meta["response_text"] == "Черновик"
    assert stat.stats.llm_requests == 1


def test_apply_final_llm_reject():
    stat = CollectStatService()
    items = [_make_filter_result("102", description="нужен отказ")]

    async def fake_evaluate(order, envs=None):
        return FinalResponseResult(
            order_id="102",
            should_respond=False,
            reject_reason="Не наш профиль",
        )

    with patch("src.use_cases.envs.ENABLE_FINAL_LLM", True), patch(
        "src.use_cases.envs.FINAL_LLM_MAX_ORDERS", 1
    ), patch("src.use_cases.evaluate_order", side_effect=fake_evaluate):
        approved, rejected_ids, skipped = _apply_final_llm_filtering(items, stat)

    assert not approved
    assert rejected_ids == {"102"}
    assert len(skipped) == 1
    assert skipped[0].order.meta[FINAL_RESPONSE_META_KEY]["reject_reason"] == "Не наш профиль"


def test_apply_final_llm_respects_max_orders():
    stat = CollectStatService()
    items = [_make_filter_result("201"), _make_filter_result("202")]

    async def fake_evaluate(order, envs=None):
        return FinalResponseResult(
            order_id=order.id,
            should_respond=True,
            response_text="ok",
            execution_days=1,
            price=1,
        )

    with patch("src.use_cases.envs.ENABLE_FINAL_LLM", True), patch(
        "src.use_cases.envs.FINAL_LLM_MAX_ORDERS", 1
    ), patch("src.use_cases.evaluate_order", side_effect=fake_evaluate):
        approved, rejected_ids, skipped = _apply_final_llm_filtering(items, stat)

    assert len(approved) == 2
    assert approved[0].order.meta.get(FINAL_RESPONSE_META_KEY)
    assert not approved[1].order.meta
    assert stat.stats.llm_requests == 1


def test_apply_final_llm_disabled():
    stat = CollectStatService()
    items = [_make_filter_result("301")]

    with patch("src.use_cases.envs.ENABLE_FINAL_LLM", False):
        approved, rejected_ids, skipped = _apply_final_llm_filtering(items, stat)

    assert approved == items
    assert not rejected_ids
    assert not skipped
    assert stat.stats.llm_requests == 0


def test_apply_final_llm_api_error_fail_open():
    stat = CollectStatService()
    items = [_make_filter_result("401")]

    async def boom(order, envs=None):
        raise RuntimeError("api down")

    with patch("src.use_cases.envs.ENABLE_FINAL_LLM", True), patch(
        "src.use_cases.envs.FINAL_LLM_MAX_ORDERS", 1
    ), patch("src.use_cases.evaluate_order", side_effect=boom):
        approved, rejected_ids, skipped = _apply_final_llm_filtering(items, stat)

    assert len(approved) == 1
    assert not approved[0].order.meta
    assert not rejected_ids
    assert not skipped
