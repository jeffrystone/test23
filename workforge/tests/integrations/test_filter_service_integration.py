import pytest

from src import container as ct
from src.common.dto import ColorsEnum, Order, OrderFilterResult

POSITIVE_KEYWORDS_CONTENT = """кабинет
подписк
тариф
договор
платеж
эквайринг
счет
регистрац
авторизац
вход по
роль
админк
управлен
интеграц
база данных
баз данных
базе данных
базу данных
синхронизац
импорт
загрузк
экспор
выгрузк
уведомлен
статус
workflow
автоматизац
склад
остатки
доставк
бронирован
расписан
календар
учет
учёт
отчет
дашборд
модерац
поддержк
приложен
replit
cursor
архитектур
python
git
нейросет
llm
фронт
frontend
бэк
backend
vue
rag
эмбеддинг
embedding
mvp
fastapi
postgres
mysql
saas
react
next
typescript
java
домен
скрипт
систем
корпорат
промт
промпт
prompt
чатбот
аудит
продукт"""

NEGATIVE_KEYWORDS_CONTENT = """лого
баннер
обложк
визитк
буклет
листовк
ux/ui
ui/ux
дизайн сайт
дизайна сайт
редизайн
презентац
иллюстрац
креатив
анимац
3dsmax
fbx
blender
мокап
reels
tiktok
инстаграм
instagram
шортс
монтаж
съемк
копирайтер
seo
яндекс.метрик
яндекс метрик
google analytics
продвижен
директ
я.директ
яндекс.директ
ads
таргет
рекламн
лид
маркетолог
smm
вордпрес
wordpress
joomla
tilda
тильд
битрикс
bitrix
amo crm
прозвон
генплан
смет
арбитраж
арбетраж
взлом
ролик
материал
канал
промоутинг
UGC
лэндинг
лендинг
посадочн
ремонт
чертеж
рассыл
нарисовать
перерисовать
отрисовать
рисованн
рисовать
значк
modx
буклет
банер
баннер
стикерпак
брошюра
интерьер
референс
1C
1С
отзыв
визуал
брендбук
brandbook
сообществ
8 марта
23 февраля
инвайт
селлер
wildberries
озон
ozon
литератур
аранжировк
партитур
стенд
дизайнер
левел-дизайнер
ценовые групп
ценовых групп
свадьб
вотермарк
watermark
max
нейминг
слоган
фирменные цвета
полиграф
laravel
первое касание
сбор контактов
поиск клиентов
написать описание
продающ
сценари
ИИ видео
ИИ-видео
AI видео
AI-видео
одностраничн
айдентик
mexc
спот
усидчивость
внимательность
заполнить
наполнить
повторить
шкаф
юзабилити анализ
solidworks
издели
конверси
магистр
практик
диплом
курсовая
курсовые
курсовой
плагиат
задачек
задачки
иконок
иконк
холодн
рассылк
таргетолог
изготовлен
произведени
карандаш
портрет
траффер
худож
загородн
фирменный стиль
фирменного стиля
в стиле
меню для
таплинк
taplink
продамус
автоворонк
pinterest
помещени
площадь
3D-аниматор
стать
блог
знаков
elementor
только дизайн
дизайн-проект
трупп
репертуар
афиш
дизайна упаковки
дизайн упаковки
регламент
аватар
привлечь
заставк
офлайн-мероприят
ОВиК
газовый котел
прослуш
прослушк
перехват
запись разговор
умная колонка
спам
антиспам
почтовый сервер
почтового сервера
php
привлечен
в команду
менеджер по продажам
esp32
arduino
stm32
микроконтроллер
pcb
разводк
датчик
по примеру
металлоконструкц
металлокаркас
навес
стеклян
козырек
пергола
псд
железобетон
autocad
автокад
архикад
армирован
archicad
dwg
эвакуац
сделать коммерческ
составить коммерческ
создать коммерческ
разработать коммерческ
создание коммерческ
разработка коммерческ
составление коммерческ
сделать кп
составить кп
создать кп
разработать кп
создание кп
разработка кп
составление кп
копирайтер
исключить данные
решения проблем
решение проблем
провокационн
юрист
адвокат
161-фз
152-фз
44-фз
223-фз
досудебн
revit
статуэт
фигур
баг
исправлен
несложн
правк
глаз
носа
перевести
voice-over
субтитр
"""
#опубликовать

STOP_KEYWORDS_CONTENT = """яндекс.метрик
яндекс метрик
вордпресс
wordpress
joomla
tilda
amo crm
арбитраж
арбетраж
аутрич
"""

# я.директ
# тильд

orders = [

    Order(
        id="1",
        name="Нужна интеграция по договору",
        description="Сделать логотип для нового кабинета",
        url="https://example.com/order/1",
    ),
    Order(
        id="5492367",
        name="Создать РК для сайта по строительству каркасных домов",
        description="Есть сайт по строительству каркасных домов, он на тильде, требует небольших корректировок по наполнению и контенту (сделаю в ближайшее время), но весь посыл на нем будет...",
        url="https://fl.ru/projects/5492367/sozdat-rk-dlya-sayta-po-stroitelstvu-karkasnyih-domov.html",
        meta={
            "qa_project_name": "project-item5492367",
            "data_id": "qa-lenta-1",
            "price": "по договоренности",
            "image_urls": [],
            "answers": "Нет ответов",
            "views": 19,
            "time_posted": "1 минуту назад",
        },
    ),
    Order(
        id="1",
        name="Отрисовка макетов экранов приложения по доставке воды",
        description="Необходимо отрисовать макеты экранов приложения по доставке воды. Дизайн должен быть удобен, визуально приятен и учитывать опыт успешных решений других приложений (UX/UI)....",
        url="https://example.com/order/1",
    ),

    Order(
        id="1",
        name="Сформировать отчет из программы Seldon и предоставить выгрузку в формате .xslx",
        description="Сделать .xlsx выгрузку по отчету “Реестр закупок с контрактами и протоколами”.  ## Фильтры  1. ФЗ-44, ФЗ-223 2. ОКПД: 62 или 63.11 (включая подгруппы) 3. Дата начала приема...",
        url="https://example.com/order/1",
    ),
    Order(
        id="1",
        name="собрать и сегментировать базу строительных компаний РФ под B2B-аутрич",
        description="Целевые сегменты: Реконструкция / капремонт / модернизация / действующие объекты Генподряд / строительство под ключ / полный цикл Fit-out / отделка и ремонт коммерческих...",
        url="https://example.com/order/1",
    ),
    Order(
        id="1",
        name="Нужен веб-дизайнер (UX + премиальный B2B стиль) для сайта советника собственников бизнеса",
        description="Ищу дизайнера с опытом в B2B / премиум-сегменте (аудитория — собственники МСБ, состоятельные предприниматели). Задача — разработать дизайн сайта по готовой архитектуре и...",
        url="https://example.com/order/1",
    ),
    Order(
        id="1",
        name="Ведение я.директ",
        description="Задача: с нуля запустить РСЯ на чат-бот (воронка)  KPI: первый месяц лид до 800р.(подписка на бот). Цель выйти на 200-300р. Долгосрочное сотрудничество, если показываете...",
        url="https://example.com/order/1",
    ),
    Order(
        id="1",
        name="Создать форму на Тильде для онлайн-оплаты услуг с произвольной суммой",
        description="Создать форму с полями на Тильде 1. Фио 2. Емайл 3. Телефон 4. Произвольная сумма 5. Галочка согласие с политикой конфиденциальности  Далее перебрасывало миную корзину (а в...",
        url="https://example.com/order/1",
    ),
    Order(
        id="1",
        name="Опубликовать отзыв на Яндексе",
        description="Нужно опубликовать один отзыв на Яндекс картах со своего личного аккаунта.  Готовый текст и ссылку на организацию отправлю.  Оплата спустя три дня после размещения отзыва и...",
        url="https://example.com/order/1",
    ),
]


@pytest.mark.parametrize(
    "order,expected_result",
    [
        (
            orders[0],
            OrderFilterResult(
                order=orders[0],
                count_positive_keywords=3,
                count_negative_keywords=1,
                send_to_telegram=False,
                filter_with_llm=True,
                telegram_message_color=ColorsEnum.green,
            ),
        ),
        (
            orders[1],
            OrderFilterResult(
                order=orders[1],
                count_positive_keywords=0,
                count_negative_keywords=1,
                send_to_telegram=False,
                filter_with_llm=True,
                telegram_message_color=ColorsEnum.red,
            ),
        ),
        (
            orders[2],
            OrderFilterResult(
                order=orders[2],
                count_positive_keywords=2,
                count_negative_keywords=3,
                count_stop_keywords=0,
                send_to_telegram=False,
                filter_with_llm=True,
                telegram_message_color=ColorsEnum.yellow,
            ),
        ),
        (
                orders[3],
                OrderFilterResult(
                    order=orders[3],
                    count_positive_keywords=2,
                    count_negative_keywords=0,
                    count_stop_keywords=0,
                    send_to_telegram=False,
                    filter_with_llm=True,
                    telegram_message_color=ColorsEnum.green,
                ),
        ),
        (
                orders[4],
                OrderFilterResult(
                    order=orders[4],
                    count_positive_keywords=0,
                    count_negative_keywords=1,
                    count_stop_keywords=0,
                    send_to_telegram=False,
                    filter_with_llm=True,
                    telegram_message_color=ColorsEnum.red,
                ),
        ),
        (
                orders[5],
                OrderFilterResult(
                    order=orders[5],
                    count_positive_keywords=2,
                    count_negative_keywords=2,
                    count_stop_keywords=0,
                    send_to_telegram=False,
                    filter_with_llm=True,
                    telegram_message_color=ColorsEnum.yellow,
                ),
        ),
        (
                orders[6],
                OrderFilterResult(
                    order=orders[6],
                    count_positive_keywords=1,
                    count_negative_keywords=3,
                    count_stop_keywords=0,
                    send_to_telegram=False,
                    filter_with_llm=True,
                    telegram_message_color=ColorsEnum.yellow,
                ),
        ),
        (
                orders[7],
                OrderFilterResult(
                    order=orders[7],
                    count_positive_keywords=0,
                    count_negative_keywords=1,
                    count_stop_keywords=0,
                    send_to_telegram=False,
                    filter_with_llm=True,
                    telegram_message_color=ColorsEnum.red,
                ),
        ),
        (
                orders[8],
                OrderFilterResult(
                    order=orders[8],
                    count_positive_keywords=0,
                    count_negative_keywords=1,
                    count_stop_keywords=0,
                    send_to_telegram=False,
                    filter_with_llm=True,
                    telegram_message_color=ColorsEnum.red,
                ),
        ),
    ],
)
def test_filter_service_filters_order_with_real_keyword_files(
    order: Order,
    expected_result: OrderFilterResult,
    tmp_path,
    monkeypatch,
):
    positive_keywords_file = tmp_path / "positive_keywords.txt"
    negative_keywords_file = tmp_path / "negative_keywords.txt"
    stop_keywords_file = tmp_path / "stop_keywords.txt"

    positive_keywords_file.write_text(POSITIVE_KEYWORDS_CONTENT)
    negative_keywords_file.write_text(NEGATIVE_KEYWORDS_CONTENT)
    stop_keywords_file.write_text(STOP_KEYWORDS_CONTENT)

    monkeypatch.setattr(ct, "POSITIVE_KEYWORDS_PATH", str(positive_keywords_file))
    monkeypatch.setattr(ct, "NEGATIVE_KEYWORDS_PATH", str(negative_keywords_file))
    monkeypatch.setattr(ct, "STOP_KEYWORDS_PATH", str(stop_keywords_file))

    filter_service = ct.get_filter_service()
    result = filter_service.filter(order)

    assert result.order == expected_result.order
    assert result.count_positive_keywords == expected_result.count_positive_keywords
    assert result.count_negative_keywords == expected_result.count_negative_keywords
    assert result.send_to_telegram is expected_result.send_to_telegram
    assert result.filter_with_llm is expected_result.filter_with_llm
    assert result.telegram_message_color == expected_result.telegram_message_color
