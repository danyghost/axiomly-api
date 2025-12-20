import json
from typing import Dict, List


class CityRegionMapper:
    def __init__(self, json_path: str):
        with open(json_path, 'r', encoding='utf-8') as f:
            self.region_to_cities: Dict[str, List[str]] = json.load(f)

        # Создаём обратный маппинг город -> регион
        self.city_to_region = {}
        for region, cities in self.region_to_cities.items():
            for city in cities:
                self.city_to_region[city.lower()] = region

    def get_region_from_city(self, city: str) -> str:
        """Возвращает регион по названию города"""
        return self.city_to_region.get(city.lower(), "Неизвестный регион")

    def get_cities_by_region(self, region: str) -> List[str]:
        """Возвращает список городов в регионе"""
        return self.region_to_cities.get(region, [])