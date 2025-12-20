import requests
from typing import List, Dict, Any
import json
import re
import time
from bs4 import BeautifulSoup
import cianparser
import logging

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
}

_CAPTCHA_MARKERS = (
    "captcha",
    "капча",
    "проверка безопасности",
    "security check",
    "доступ ограничен",
    "подозрительная активность",
    "robot",
)

def _looks_like_captcha(html: str) -> bool:
    if not html:
        return True
    low = html.lower()
    return any(m in low for m in _CAPTCHA_MARKERS)


# Загружаем маппинг город->регион
def load_region_mapping(mapping_path='regions.json'):
    """Загружает маппинг регионов и городов"""
    try:
        with open(mapping_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("Файл %s не найден", mapping_path)
        return {}
    except json.JSONDecodeError:
        logger.warning("Ошибка JSON в файле %s", mapping_path)
        return {}


# Создаем обратный маппинг город->регион
def create_city_to_region_mapping(region_data):
    """Создает маппинг город -> регион"""
    city_to_region = {}
    for region, cities in region_data.items():
        for city in cities:
            city_to_region[city.lower()] = region
    return city_to_region

# Загружаем данные при импорте
region_data = load_region_mapping()
city_to_region_mapping = create_city_to_region_mapping(region_data)

def get_region_from_city(city_name):
    """Определяет регион по названию города"""
    if not city_name:
        return "Неизвестный регион"
    return city_to_region_mapping.get(city_name.lower(), "Неизвестный регион")


def get_city_id(city_name, valid_locations):
    """Получает ID города из списка cianparser"""
    for loc in valid_locations:
        if isinstance(loc, list) and len(loc) >= 2 and loc[0].lower() == city_name.lower():
            return loc[1]  # Возвращаем ID
    return None

def parse_cian_page(url, params, DEFAULT_HEADERS, deal_type):
    """Парсит одну страницу CIAN с учетом типа сделки"""
    try:
        response = requests.get(url, params=params, headers=DEFAULT_HEADERS, timeout=15)
        if response.url and "captcha" in response.url.lower():
            logger.warning("Циан редирект на капчу url=%s", response.url)
            return []

        # Fail-safe: редиректы/403/429/5xx — сразу считаем, что аналогов нет
        if response.status_code in (403, 429) or response.status_code >= 500:
            logger.warning("Циан статус=%s for %s params=%s", response.status_code, url, params)
            return []

        response.raise_for_status()

        html = response.text or ""
        if _looks_like_captcha(html):
            logger.warning("Циан Выглядит как капча/блок для %s params=%s", url, params)
            return []

        soup = BeautifulSoup(html, "html.parser")

        cards = soup.find_all("article", {"data-name": "CardComponent"})
        if not cards and deal_type == "rent":
            cards = soup.find_all("div", {"data-name": "OfferCard"})

        if not cards:
            logger.info("Не найдено карточек для deal_type=%s url=%s params=%s", deal_type, url, params)
            return []

        analogs = []
        for card in cards:
            try:
                # Извлекаем цену - разные селекторы для аренды и продажи
                price_elem = None

                if deal_type == 'sale':
                    # Для продажи
                    price_elem = (card.find('span', {'data-mark': 'MainPrice'}) or
                                  card.find('span', class_=re.compile(r'price', re.I)))
                else:
                    # Для аренды
                    price_elem = (card.find('span', {'data-mark': 'MainPrice'}) or
                                  card.find('span', class_=re.compile(r'price|rent', re.I)) or
                                  card.find('p', class_=re.compile(r'price', re.I)))

                if not price_elem:
                    continue

                price_text = price_elem.get_text()
                # Очищаем цену и учитываем, что аренда может быть в руб/мес
                price_text_clean = re.sub(r'[^\d]', '', price_text.split('/')[0])  # Берем часть до "/"
                price = float(price_text_clean) if price_text_clean else 0

                if price == 0:
                    continue

                # Извлекаем площадь
                area_elem = card.find('div', string=re.compile(r'м²'))
                if not area_elem:
                    # Альтернативные поиски площади
                    area_elems = card.find_all('div', string=re.compile(r'(\d+[,.]?\d*)\s*м²'))
                    if area_elems:
                        area_elem = area_elems[0]

                area_val = None
                if area_elem:
                    area_text = area_elem.get_text()
                    area_match = re.search(r'(\d+[,.]?\d*)\s*м²', area_text)
                    if area_match:
                        area_val = float(area_match.group(1).replace(',', '.'))

                # Извлекаем количество комнат
                rooms_elem = card.find('div', string=re.compile(r'-комн|комнат|комн|Студия'))
                rooms_val = None
                if rooms_elem:
                    rooms_text = rooms_elem.get_text()
                    # Обработка студий
                    if 'студия' in rooms_text.lower() or 'studio' in rooms_text.lower():
                        rooms_val = 0
                    else:
                        rooms_match = re.search(r'(\d+)\s*[-]?комн', rooms_text)
                        if rooms_match:
                            rooms_val = int(rooms_match.group(1))

                # Извлекаем адрес
                address_elem = card.find('div', {'data-name': 'AddressContainer'})
                if not address_elem:
                    address_elem = card.find('a', {'data-name': 'Link'})  # Иногда адрес в ссылке

                address = address_elem.get_text().strip() if address_elem else ''

                # Извлекаем ссылку
                link_elem = card.find('a', {'data-name': 'Link'})
                if not link_elem:
                    link_elem = card.find('a', href=re.compile(r'cian.ru/rent/flat|cian.ru/sale/flat'))

                url = link_elem['href'] if link_elem and link_elem.has_attr('href') else ''
                if url and not url.startswith('http'):
                    url = 'https://www.cian.ru' + url

                # Извлекаем этаж
                floor_elem = card.find('div', string=re.compile(r'этаж'))
                floor_info = ''
                if floor_elem:
                    floor_info = floor_elem.get_text().strip()

                analog_data = {
                    'price': price,
                    'area_total': area_val,
                    'rooms': rooms_val,
                    'address': address,
                    'url': url,
                    'floor_info': floor_info,
                    'deal_type': deal_type
                }

                # Валидация минимальных требований
                if price > 0 and area_val and area_val > 10:  # Минимальная площадь 10 м²
                    analogs.append(analog_data)

            except Exception:
                logger.debug("Ошибка парсинга карточки", exc_info=True)
                continue

        return analogs

    except Exception:
        logger.warning("Ошибка парсинга страницы url=%s params=%s", url, params, exc_info=True)
        return []

def get_cian_analogs(
        location: str,
        deal_type: str,
        rooms: int,
        area: float,
        start_page: int = 1,
        end_page: int = 1
) -> List[Dict[str, Any]]:
    """
    Парсит аналоги с CIAN для аренды или продажи
    """

    # Получаем ID города через cianparser
    valid_locations = cianparser.list_locations()
    city_id = get_city_id(location, valid_locations)

    if not city_id:
        logger.info("Не найден city_id для города '%s'", location)
        return []

    logger.info("Парсинг Циан: city=%s city_id=%s deal_type=%s rooms=%s area=%s",
                location, city_id, deal_type, rooms, area)

    all_analogs = []
    base_url = "https://www.cian.ru/cat.php"

    # Настройки парсинга в зависимости от типа сделки
    max_pages = 2 if deal_type == 'rent' else 3  # Меньше страниц для аренды
    end_page = min(end_page, max_pages)

    for page in range(start_page, end_page + 1):
        logger.debug("Парсим страницу=%s deal_type=%s", page, deal_type)

        # Базовые параметры
        params = {
            'deal_type': deal_type,
            'engine_version': 2,
            'offer_type': 'flat',
            'region': city_id,
            'p': page,
        }

        # Параметры комнат в зависимости от типа
        if rooms == 0:  # Студия
            params['room9'] = 1  # Студии
        elif rooms >= 1 and rooms <= 3:
            params[f'room{rooms}'] = 1
        else:  # 4+ комнаты
            params['room4'] = 1

        # Дополнительные параметры для уточнения поиска
        params['mintarea'] = max(area * 0.7, 20)  # Минимальная площадь -70%
        params['maxtarea'] = area * 1.2  # Максимальная площадь +20%

        try:
            logger.debug("Парсинг страницы=%s deal_type=%s params=%s", page, deal_type, params)

            analogs = parse_cian_page(base_url, params, DEFAULT_HEADERS, deal_type)

            if not analogs:
                logger.info("Нет аналогов на странице Циан=%s (stop)", page)
                if page == start_page:
                    return []
                break

            all_analogs.extend(analogs)
            logger.debug("Найдено на странице=%s: %s", page, len(analogs))

            time.sleep(0)

            if len(analogs) < 5 and page > start_page:
                logger.info("Несколько предложений на странице=%s (found=%s), stop", page, len(analogs))
                break

        except Exception:
            logger.warning("Ошибка парсинга страницы=%s", page, exc_info=True)
            continue

    logger.info("Всего найдено объявлений для %s: %s", deal_type, len(all_analogs))

    # Фильтрация и сортировка результатов
    if not all_analogs:
        return []

    # Фильтруем по площади (±20%)
    area_tol = area * 0.2
    filtered_analogs = [
        flat for flat in all_analogs
        if flat['area_total'] and abs(flat['area_total'] - area) <= area_tol
    ]

    logger.info("После фильтрации по площади: %s объявлений", len(filtered_analogs))

    # Сортировка по похожести (более строгая для аренды)
    def similarity(flat):
        flat_area = flat.get('area_total', 0)
        flat_rooms = flat.get('rooms', -1)

        # Весовые коэффициенты в зависимости от типа сделки
        if deal_type == 'rent':
            area_weight = 2.0  # Больший вес площади для аренды
            rooms_weight = 1.5
        else:
            area_weight = 1.0
            rooms_weight = 1.0

        area_diff = abs(flat_area - area) * area_weight if flat_area else 1000
        rooms_diff = abs(flat_rooms - rooms) * 10 * rooms_weight if flat_rooms != -1 else 500

        return area_diff + rooms_diff

    filtered_analogs.sort(key=similarity)

    # Добавляем информацию о городе и регионе
    for flat in filtered_analogs:
        flat['city'] = location
        flat['region'] = get_region_from_city(location)
        # Добавляем форматированную цену для отображения
        flat['price_formatted'] = f"{flat['price']:,.0f}".replace(',', ' ')

    # Возвращаем наиболее похожие аналоги (больше для аренды)
    max_results = 10 if deal_type == 'rent' else 7
    return filtered_analogs[:max_results]