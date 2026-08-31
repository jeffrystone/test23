import logging
from typing import Generator

from pydantic import ValidationError

from src.common import consts
from src.common.cookies import load_cookies, save_json
from src.common.dto import Order
from src.common.scrap import lazy_paginated_scrapping

from .parser import fl_board_parser, fl_next_page_exist, fl_paginated_url

logger = logging.getLogger(__name__)


def parse_fl_board() -> Generator:

    base_url = "https://fl.ru"
    cookies_url = "https://www.fl.ru/user/modals/my/"

    headers = consts.HEADERS
    cookies = load_cookies(cookies_url, headers, "./staticfiles/fl")
    if not {"XSRF-TOKEN", "PHPSESSID"}.issubset(cookies.keys()):
        logger.critical(
            "Cookies do not contain authorization data. Current cookies %s", cookies
        )

    gen = lazy_paginated_scrapping(
        base_url,
        headers,
        cookies,
        fl_paginated_url,
        fl_board_parser,
        fl_next_page_exist,
    )

    for projects in gen:

        validated_projects = []

        for item in projects:
            try:
                ord = Order(
                    id=item["id"],
                    name=item["title"],
                    description=item["description"],
                    url=base_url + item["url"],
                    meta={
                        k: v
                        for k, v in item.items()
                        if k not in ["id", "title", "description", "url"]
                    },
                )
            except (KeyError, ValidationError) as e:
                logger.warning(e, extra=item)
            else:
                validated_projects.append(ord)

        yield validated_projects
