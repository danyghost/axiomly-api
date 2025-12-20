from core.parsers.cian_parser import get_cian_analogs

def get_analogs(city: str, deal_type: str, rooms: int, area: float):
    return get_cian_analogs(
        location=city,
        deal_type=deal_type,
        rooms=rooms,
        area=area,
        start_page=1,
        end_page=1,
    )