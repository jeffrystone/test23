import argparse
import json
import logging
import sys
from pathlib import Path

from final_response.config import FinalResponseEnvs
from final_response.logging_config import LOG_FILE, setup_logging
from final_response.schemas import OrderInput
from final_response.service import evaluate_order_sync

logger = logging.getLogger(__name__)

REJECT_EXIT_CODE = 2


def project_to_order_input(project: dict) -> OrderInput:
    files = project.get("files") or []
    meta = {"files": files} if files else None
    return OrderInput(
        id=str(project.get("id") or "unknown"),
        name=str(project.get("name") or "Заказ"),
        description=str(project.get("summary") or project.get("description") or ""),
        url=str(project.get("url") or ""),
        meta=meta,
    )


def result_to_order_response(project: dict, result) -> dict:
    examples = [item["path"] for item in project.get("files", []) if item.get("path")][:3]
    return {
        "summary": result.response_text or "",
        "days": result.execution_days or 0,
        "estimate_cost": result.price or 0,
        "examples": examples,
    }


def resolve_mode(cli_mode: str | None) -> str:
    if cli_mode:
        return cli_mode.strip().lower()
    return FinalResponseEnvs().AI_MODE.strip().lower()


def main():
    setup_logging()

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--mode",
        choices=["mock", "yandex", "claude"],
        help="Провайдер ИИ (перекрывает AI_MODE из .env, по умолчанию mock)",
    )
    args = parser.parse_args()

    project = json.loads(Path(args.input).read_text(encoding="utf-8"))
    mode = resolve_mode(args.mode)
    envs = FinalResponseEnvs(AI_MODE=mode)
    order = project_to_order_input(project)

    logger.info(
        "Run mode=%s input=%s output=%s order_id=%s log=%s",
        mode,
        args.input,
        args.output,
        order.id,
        LOG_FILE,
    )

    try:
        result = evaluate_order_sync(order, envs=envs)
    except ValueError as exc:
        logger.error("Provider error: %s", exc)
        sys.exit(1)
    except Exception as exc:
        logger.exception("AI call failed: %s", exc)
        sys.exit(1)

    if not result.should_respond:
        logger.info(
            "Reject order_id=%s reason=%s",
            result.order_id,
            result.reject_reason or "no reason",
        )
        sys.exit(REJECT_EXIT_CODE)

    response = result_to_order_response(project, result)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(response, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info(
        "Approve order_id=%s days=%s estimate_cost=%s output=%s",
        result.order_id,
        response["days"],
        response["estimate_cost"],
        output,
    )


if __name__ == "__main__":
    main()
