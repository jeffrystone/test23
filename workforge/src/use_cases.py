import asyncio
import logging

from src.common import dto, llm, telegram_senders
from src.common import dto_msg_converters as converters
from src.schemas import ClassifiedOrder, ClassifiedOrderBatch

from src.container import async_openai_client, envs, prompts, get_repo, get_order_page_service
from src.fl.main import parse_fl_board, get_fl_cookies
from src.fl.offer_mode import is_auto_offer
from src.fl.offer_submitter import OfferSubmitter
from src.common import consts
from src.common.repos import AbstractOrderRepo
from src.common.dto import OrderFilterResult, RunStats
from src.common.services.collect_stat_service import CollectStatService
from src.final_response.config import FinalResponseEnvs
from src.final_response.assemble import assemble_response
from src.final_response.schemas import OrderInput
from src.final_response.service import evaluate_order
from src.container import get_filter_service, get_stat_service

logger = logging.getLogger("app")
LLM_CLASSIFICATION_META_KEY = "llm_classification"
FINAL_RESPONSE_META_KEY = "final_response"
OFFER_RESULT_META_KEY = "offer_result"


def order_to_final_response_input(order: dto.Order) -> OrderInput:
    return OrderInput(
        id=order.id,
        name=order.name,
        description=order.description,
        url=order.url,
        meta=order.meta,
    )


def classify(
    data: list[dto.OrderList], stat_service: CollectStatService
) -> ClassifiedOrderBatch:
    main_prompt = prompts.get_prompt("main", True)

    async def run_async():
        async def classify_one(item: dto.OrderList):

            messages = [
                {"role": "system", "content": main_prompt},
                {"role": "user", "content": item.model_dump_json()},
            ]
            stat_service.add_llm_requests_count(len(item.orders))
            return await llm.generate(
                client=async_openai_client,
                validation_class=ClassifiedOrderBatch,
                messages=messages,
                model=envs.DEFAULT_OPENAI_MODEL,
                response_format={"type": "json_object"},
            )

        return await asyncio.gather(
            *[classify_one(it) for it in data],
        )

    if envs.ENABLE_CLASSIFICATION:
        result: list[ClassifiedOrderBatch] = asyncio.run(run_async())
    else:
        result = [
            ClassifiedOrderBatch(
                items=[ClassifiedOrder(id=order.id, approved=True, reason="_") for order in batch.orders]
            )
            for batch in data
        ]

    combined = ClassifiedOrderBatch(items=[])

    for res in result:
        if isinstance(res, ClassifiedOrderBatch):
            combined.items.extend(res.items)
        else:
            logger.warning("Unexpected classification response type: %s", type(res).__name__)

    return combined


def remove_processed_project_ids(orders: list[dto.Order], repo: AbstractOrderRepo):
    ids_orders_mapping = {order.id: order for order in orders}
    unprocessed = repo.check_unprocessed(ids_orders_mapping.keys())
    return [ids_orders_mapping[_id] for _id in unprocessed]


def _collect_unprocessed_orders(repo: AbstractOrderRepo) -> dto.OrderList:
    data = dto.OrderList(orders=[])
    for orders in parse_fl_board():
        need_to_process = remove_processed_project_ids(orders, repo=repo)
        if not need_to_process:
            continue
        data.orders.extend(need_to_process)
    return data


def _split_by_filtering_requirements(
    orders: list[dto.Order],
) -> tuple[list[OrderFilterResult], list[OrderFilterResult], list[OrderFilterResult]]:

    send_without_filtering: list[OrderFilterResult] = []
    need_llm_filtering: list[OrderFilterResult] = []
    skip_sending: list[OrderFilterResult] = []
    filter_service = get_filter_service()

    for order in orders:
        processed_order: OrderFilterResult = filter_service.filter(order)

        if processed_order.send_to_telegram:
            send_without_filtering.append(processed_order)
            continue

        if processed_order.filter_with_llm:
            need_llm_filtering.append(processed_order)
            continue

        skip_sending.append(processed_order)

    return send_without_filtering, need_llm_filtering, skip_sending


def _apply_llm_filtering(
    need_llm_filtering: list[OrderFilterResult], stat_service
) -> tuple[
    list[OrderFilterResult],
    set[str],
    list[OrderFilterResult],
]:
    if not need_llm_filtering:
        return [], set(), []

    filtered_with_llm_orders: ClassifiedOrderBatch = classify(
        [dto.OrderList(orders=[it.order for it in need_llm_filtering])], stat_service=stat_service
    )

    llm_results_mapping = {it.order.id: it for it in need_llm_filtering}
    orders_after_llm_filtering: list[OrderFilterResult] = []
    llm_rejected_ids: set[str] = set()
    skipped: list[OrderFilterResult] = []
    for classified_order in filtered_with_llm_orders.items:
        result = llm_results_mapping.pop(classified_order.id, None)
        if not result:
            logger.warning(
                "LLM returned classification for unknown order id: %s",
                classified_order.id,
            )
            continue

        if result.order.meta is None:
            result.order.meta = {}
        result.order.meta[LLM_CLASSIFICATION_META_KEY] = classified_order.model_dump(
            exclude_none=True
        )

        if classified_order.approved:
            orders_after_llm_filtering.append(result)
        else:
            llm_rejected_ids.add(result.order.id)
            skipped.append(result)

    # If model omitted some ids, keep them as skipped by LLM so they are visible in stats.
    skipped.extend(llm_results_mapping.values())

    return orders_after_llm_filtering, llm_rejected_ids, skipped

def _enrich_orders_for_final_llm(
    orders_for_sending: list[OrderFilterResult],
) -> None:
    if not envs.ENABLE_FINAL_LLM or not orders_for_sending:
        return

    service = get_order_page_service()
    cookies = get_fl_cookies()
    candidates = orders_for_sending[: envs.FINAL_LLM_MAX_ORDERS]
    enriched_orders = service.enrich_orders(
        [item.order for item in candidates],
        cookies=cookies,
        headers=consts.HEADERS,
        max_count=envs.FINAL_LLM_MAX_ORDERS,
    )
    for item, enriched in zip(candidates, enriched_orders):
        item.order = enriched


def _apply_final_llm_filtering(
    orders_for_sending: list[OrderFilterResult],
    stat_service: CollectStatService,
) -> tuple[list[OrderFilterResult], set[str], list[OrderFilterResult]]:
    if not envs.ENABLE_FINAL_LLM or not orders_for_sending:
        return orders_for_sending, set(), []

    candidates = orders_for_sending[: envs.FINAL_LLM_MAX_ORDERS]
    rest = orders_for_sending[len(candidates) :]
    if not candidates:
        return orders_for_sending, set(), []

    final_envs = FinalResponseEnvs()
    stat_service.add_llm_requests_count(len(candidates))

    async def run_async():
        return await asyncio.gather(
            *[
                evaluate_order(
                    order_to_final_response_input(item.order),
                    envs=final_envs,
                )
                for item in candidates
            ],
            return_exceptions=True,
        )

    results = asyncio.run(run_async())

    approved: list[OrderFilterResult] = []
    final_llm_rejected_ids: set[str] = set()
    skipped: list[OrderFilterResult] = []

    for item, result in zip(candidates, results):
        if isinstance(result, BaseException):
            logger.warning(
                "Final LLM failed for order %s: %s",
                item.order.id,
                result,
                exc_info=result,
            )
            approved.append(item)
            continue

        if item.order.meta is None:
            item.order.meta = {}
        meta = result.model_dump(exclude_none=True)
        if result.should_respond:
            try:
                meta["full_text"] = assemble_response(
                    result.response_text or "",
                    signature_path=final_envs.RESPONSE_SIGNATURE_FILE,
                )
            except Exception as exc:
                logger.warning(
                    "Response assembly failed for order %s: %s",
                    item.order.id,
                    exc,
                )
        item.order.meta[FINAL_RESPONSE_META_KEY] = meta

        if result.should_respond:
            approved.append(item)
        else:
            final_llm_rejected_ids.add(item.order.id)
            skipped.append(item)

    return approved + rest, final_llm_rejected_ids, skipped


def _apply_auto_offers(orders_for_sending: list[OrderFilterResult]) -> None:
    if not is_auto_offer(envs.OFFER_MODE):
        return

    submitter = OfferSubmitter()
    cookies = get_fl_cookies()
    resume_path = envs.FL_RESUME_PATH.strip() or None

    for item in orders_for_sending:
        meta = (item.order.meta or {}).get(FINAL_RESPONSE_META_KEY)
        if not meta or not meta.get("should_respond") or not meta.get("full_text"):
            continue

        page_type = (item.order.meta or {}).get("page_type", "project")
        try:
            result = submitter.submit(
                url=item.order.url,
                summary=meta["full_text"],
                days=int(meta.get("execution_days") or 0),
                cost=int(meta.get("price") or 0),
                page_type=page_type,
                cookies=cookies,
                headers=consts.HEADERS,
                resume_path=resume_path,
            )
            if item.order.meta is None:
                item.order.meta = {}
            item.order.meta[OFFER_RESULT_META_KEY] = result.model_dump(exclude_none=True)
            logger.info(
                "Auto offer for order %s: status=%s",
                item.order.id,
                result.status,
            )
        except Exception as exc:
            logger.warning(
                "Auto offer failed for order %s: %s",
                item.order.id,
                exc,
                exc_info=True,
            )
            if item.order.meta is None:
                item.order.meta = {}
            item.order.meta[OFFER_RESULT_META_KEY] = {
                "status": "error",
                "message": str(exc),
            }


def send_to_telegram_async(msgs: list[str]):
    return asyncio.run(telegram_senders.asend_messages(
        envs.TELEGRAM_BOT_TOKEN,
        envs.TELEGRAM_CHANNEL_ID,
        msgs,
        semaphore=asyncio.Semaphore(1),
    ))

def send_orders_to_telegram(
    orders_for_sending: list[OrderFilterResult], skipped_msg: bool | None = None, skipped_by_llm: bool | None = None
) -> set[str]:
    if not orders_for_sending:
        return set()

    send_results = send_to_telegram_async(
        converters.convert_filtered_to_telegram_msg(
            "FL.ru", orders_for_sending, skipped_msg=skipped_msg, skipped_by_llm=skipped_by_llm
        ),
    )

    return {
        item.order.id
        for item, response in zip(orders_for_sending, send_results)
        if isinstance(response, dict) and response.get("ok")
    }


def _mark_processed_orders(
    repo: AbstractOrderRepo,
    all_orders: list[dto.Order],
    successfully_sent_ids: set[str],
    skipped_ids: set[str],
    llm_rejected_ids: set[str],
) -> None:
    orders_ids_to_mark = successfully_sent_ids | skipped_ids | llm_rejected_ids
    orders_mapping = {order.id: order for order in all_orders}
    repo.insert_orders(
        [
            orders_mapping[order_id]
            for order_id in orders_ids_to_mark
            if order_id in orders_mapping
        ]
    )


def process_fl() -> None:
    stat_service = get_stat_service()

    try:
        _process_fl(stat_service)
    except Exception as e:
        logger.critical(e)
        stat_service.register_exception(e)

    stats = stat_service.get_actual_stats()

    if envs.SEND_SKIPPED_ORDERS and (orders := stats.skipped_orders):
        send_orders_to_telegram(orders, skipped_msg=True, skipped_by_llm=False)

    if envs.SEND_LLM_SKIPPED_ORDERS and (orders := stats.skipped_by_llm):
        send_orders_to_telegram(orders, skipped_msg=True, skipped_by_llm=True)

    if envs.SEND_DEBUG_INFO:
        stat_msg = converters.run_stats_to_msg(stats)
        send_to_telegram_async([stat_msg])


def _process_fl(stat_service: CollectStatService) -> None:
    #TODO: после полной отладки это должен превратиться в класс оркестратор
    repo = get_repo()
    data = _collect_unprocessed_orders(repo=repo)

    stat_service.save_new_orders_count(data.orders)

    logger.info("%d unprocessed offers found", len(data.orders))

    if not data.orders:
        return

    send_without_filtering, need_llm_filtering, skip_sending = (
        _split_by_filtering_requirements(data.orders)
    )
    stat_service.add_skipped(skip_sending, by_llm=False)

    orders_after_llm_filtering, llm_rejected_ids, skipped_after_filtering = (
        _apply_llm_filtering(need_llm_filtering, stat_service)
    )
    stat_service.add_skipped(skipped_after_filtering, by_llm=True)

    orders_for_sending = send_without_filtering + orders_after_llm_filtering

    _enrich_orders_for_final_llm(orders_for_sending)

    orders_for_sending, final_llm_rejected_ids, skipped_final = (
        _apply_final_llm_filtering(orders_for_sending, stat_service)
    )
    stat_service.add_skipped(skipped_final, by_llm=True)

    _apply_auto_offers(orders_for_sending)

    successfully_sent_ids = send_orders_to_telegram(orders_for_sending)
    stat_service.add_count_send(successfully_sent_ids)

    skipped_ids = {it.order.id for it in skip_sending}

    _mark_processed_orders(
        repo=repo,
        all_orders=data.orders,
        successfully_sent_ids=successfully_sent_ids,
        skipped_ids=skipped_ids,
        llm_rejected_ids=llm_rejected_ids | final_llm_rejected_ids,
    )
