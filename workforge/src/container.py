import logging

from openai import AsyncOpenAI

from src.common.prompts import Prompts
from src.common.services.collect_stat_service import CollectStatService
from src.config import Envs
from src.common.repos import SqlLiteDbOrderRepo
from src.common.db.engine import get_conn as __get_conn

from src.common.utils import get_keywords
from src.common.services.filter_service import FilterService
from src.common.keyword_counter import MarkersCounter
from src.fl.order_page_service import OrderPageService

logger = logging.getLogger(__name__)
envs = Envs()
async_openai_client = AsyncOpenAI(api_key=envs.OPENAI_KEY)
prompts = Prompts()

BD_PATH = "./staticfiles/app.db"

POSITIVE_KEYWORDS_PATH = "./staticfiles/positive_keywords.txt"
NEGATIVE_KEYWORDS_PATH = "./staticfiles/negative_keywords.txt"
STOP_KEYWORDS_PATH = "./staticfiles/stop_keywords.txt"


def get_filter_service() -> FilterService:
    positive_keywords = get_keywords(POSITIVE_KEYWORDS_PATH)
    negative_keywords = get_keywords(NEGATIVE_KEYWORDS_PATH)
    stop_keywords = get_keywords(STOP_KEYWORDS_PATH)
    logger.info(
        "Building filter service", extra={
            "positive_keywords": positive_keywords,
            "negative_keywords": negative_keywords,
            "stop_keywords": stop_keywords
        }
    )
    return FilterService(
        MarkersCounter(
            keywords=positive_keywords, name="positive_keywords"
        ),
        MarkersCounter(
            keywords=negative_keywords, name="negative_keywords"
        ),
        MarkersCounter(
            keywords=stop_keywords, name="stop_keywords"
        ),
    )

def get_stat_service() -> CollectStatService:
    return CollectStatService()


def get_conn():
    return __get_conn(BD_PATH)


def get_repo():
    return SqlLiteDbOrderRepo(get_conn())


def get_order_page_service() -> OrderPageService:
    return OrderPageService(envs.ORDER_ATTACHMENTS_DIR)
