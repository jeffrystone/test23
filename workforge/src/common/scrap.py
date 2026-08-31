import httpx


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
    response = httpx.get(url, headers=headers, cookies=cookies, follow_redirects=True)
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
