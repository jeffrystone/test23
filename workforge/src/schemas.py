from pydantic import BaseModel


class ClassifiedOrder(BaseModel):
    id: str
    approved: bool
    reason: str | None = None


class ClassifiedOrderBatch(BaseModel):
    items: list[ClassifiedOrder]