from bs4 import BeautifulSoup


def parse_project_html(project_div):
    project_data = {}

    project_data["id"] = project_div.get("id")
    project_data["qa_project_name"] = project_div.get("qa-project-name")
    project_data["data_id"] = project_div.get("data-id")

    title_tag = project_div.find("h2", class_="b-post__title")
    if title_tag:
        a_tag = title_tag.find("a")
        if a_tag:
            project_data["title"] = a_tag.get_text(strip=True)
            project_data["url"] = a_tag.get("href")

    price_tag = project_div.find("div", class_="b-post__price")
    if price_tag:
        project_data["price"] = price_tag.get_text(strip=True).replace("\xa0", " ")

    desc_tag = project_div.find("div", class_="b-post__txt text-5")
    if desc_tag:
        project_data["description"] = desc_tag.get_text(strip=True)

    images = project_div.find_all("img")
    project_data["image_urls"] = [img.get("src") for img in images if img.get("src")]

    answers_tag = project_div.find("a", class_="b-post__link_bold")
    if answers_tag:
        project_data["answers"] = answers_tag.get_text(strip=True)

    views_tag = project_div.find("span", title="Количество просмотров")
    if views_tag:
        project_data["views"] = views_tag.get_text(strip=True)

    time_tag = project_div.find("span", class_="text-gray-opacity-4")
    if time_tag:
        project_data["time_posted"] = time_tag.get_text(strip=True)

    return project_data


def fl_board_parser(html) -> list[dict]:

    soup = BeautifulSoup(html, "html.parser")
    projects_list = soup.select("#projects-list > div[data-id='qa-lenta-1']")
    all_projects = []

    for p in projects_list:
        project_data = parse_project_html(p)
        all_projects.append(project_data)

    return all_projects


def fl_next_page_exist(html, current_page: int = 1, max_page: int = 3) -> int | None:
    return current_page + 1 if max_page != current_page else None


def fl_paginated_url(base_url, page_number) -> str:
    return f"{base_url}/projects/page-{page_number}/?kind=1"
