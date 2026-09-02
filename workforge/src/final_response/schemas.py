from typing import Any

from pydantic import BaseModel


class OrderInput(BaseModel):
    id: str
    name: str
    description: str
    url: str = ""
    meta: dict[str, Any] | None = None


class LLMResponsePayload(BaseModel):
    should_respond: bool
    response_text: str | None = None
    execution_days: int | None = None
    price: int | None = None
    reject_reason: str | None = None


class FinalResponseResult(BaseModel):
    order_id: str
    should_respond: bool
    response_text: str | None = None
    execution_days: int | None = None
    price: int | None = None
    reject_reason: str | None = None
    full_text: str | None = None

    @classmethod
    def from_llm_payload(cls, order_id: str, payload: LLMResponsePayload) -> "FinalResponseResult":
        return cls(order_id=order_id, **payload.model_dump())
