import logging
from typing import Type, TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger(__name__)


async def generate(
    client: AsyncOpenAI, validation_class: Type[T], *args, **kwargs
) -> T:
    """Generate a response from OpenAI and validate it against a Pydantic model."""
    response = await client.chat.completions.create(*args, **kwargs)
    content = response.choices[0].message.content
    logger.info("%s. Result: %s", kwargs, content)
    return validation_class.model_validate_json(content)
