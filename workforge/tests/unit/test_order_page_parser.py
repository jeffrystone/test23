from bs4 import BeautifulSoup

from src.fl.order_page_parser import (
    DeadSessionError,
    detect_page_type,
    ensure_authenticated,
    parse_order_id,
    parse_order_page_html,
    sanitize_filename,
)


PROJECT_HTML = """
<html>
<head><meta name="current-uid" content="12345"></head>
<body>
  <h1 class="fl-project-content__title">Разработка API</h1>
  <div class="fl-project-content__description-text">
    <p>Нужен backend на Python.</p>
  </div>
  <div class="base-attach-class">
    <a href="/download/spec.pdf">spec.pdf</a>
  </div>
  <footer><a href="/projects/">Посмотреть другие заказы</a></footer>
</body>
</html>
"""

VACANCY_HTML = """
<html>
<head><meta name="current-uid" content="12345"></head>
<body>
  <h1 class="fl-project-content__title">Чертёжник на удалёнку</h1>
  <div class="fl-project-content__description-text">
    <p>2D чертежи.</p>
  </div>
  <footer><a href="/vacancies/">Посмотреть другие вакансии</a></footer>
</body>
</html>
"""

GUEST_HTML = """
<html>
<head><meta name="current-uid" content="0"></head>
<body><h1>Guest</h1></body>
</html>
"""


def test_sanitize_filename():
    assert sanitize_filename('bad<>name.pdf') == "bad__name.pdf"
    assert sanitize_filename("") == "file"


def test_parse_order_id():
    assert parse_order_id("https://www.fl.ru/projects/5517713/slug.html") == "5517713"
    assert parse_order_id("https://www.fl.ru/") == ""


def test_detect_page_type_project():
    soup = BeautifulSoup(PROJECT_HTML, "html.parser")
    assert detect_page_type(soup) == "project"


def test_detect_page_type_vacancy():
    soup = BeautifulSoup(VACANCY_HTML, "html.parser")
    assert detect_page_type(soup) == "vacancy"


def test_ensure_authenticated_raises_for_guest():
    soup = BeautifulSoup(GUEST_HTML, "html.parser")
    try:
        ensure_authenticated(soup)
        raise AssertionError("expected DeadSessionError")
    except DeadSessionError:
        pass


def test_parse_order_page_html_project():
    result = parse_order_page_html(
        PROJECT_HTML, "https://www.fl.ru/projects/123/test.html"
    )
    assert result.page_type == "project"
    assert result.name == "Разработка API"
    assert "backend на Python" in result.description_html
    assert len(result.attachments) == 1
    assert result.attachments[0].name == "spec.pdf"
    assert result.attachments[0].url.endswith("/download/spec.pdf")


def test_parse_order_page_html_vacancy():
    result = parse_order_page_html(
        VACANCY_HTML, "https://www.fl.ru/projects/456/test.html"
    )
    assert result.page_type == "vacancy"
    assert result.name == "Чертёжник на удалёнку"
    assert result.attachments == []


def test_parse_order_page_html_guest_raises():
    try:
        parse_order_page_html(GUEST_HTML, "https://www.fl.ru/projects/1/x.html")
        raise AssertionError("expected DeadSessionError")
    except DeadSessionError:
        pass
