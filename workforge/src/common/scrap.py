from src.common.fl_http import fl_get


def lazy_paginated_scrapping(
    base_url,
    headers,
    cookies,
    pagination_builder,
    parser_func,
    parser_pagination,
    current_page=1,
):

    url = pagination_builder(base_url, current_page)
    response = fl_get(url, headers=headers, cookies=cookies)
    html = response.text

    yield parser_func(html)

    next_page_number = parser_pagination(html, current_page)

    if next_page_number:
        yield from lazy_paginated_scrapping(
            base_url,
            headers,
            cookies,
            pagination_builder,
            parser_func,
            parser_pagination,
            next_page_number,
        )
