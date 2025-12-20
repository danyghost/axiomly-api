from fastapi import APIRouter, Request, Query

router = APIRouter()


@router.get("/locations")
def get_locations(request: Request):
    """Получение всех локаций"""
    city_mapper = request.app.state.city_mapper
    locations = []

    for region, cities in city_mapper.region_to_cities.items():
        locations.append({
            'type': 'region',
            'name': region,
            'value': region
        })
        for city in cities:
            locations.append({
                'type': 'city',
                'name': city,
                'value': city,
                'region': region,
                'parent': region
            })

    return locations


@router.get("/search-locations")
def search_locations(request: Request, q: str = Query("")):
    """Поиск локаций по названию"""
    query = q.lower().strip()
    if not query:
        return []

    city_mapper = request.app.state.city_mapper
    results = []

    for region, cities in city_mapper.region_to_cities.items():
        if query in region.lower():
            results.append({
                'type': 'region',
                'name': region,
                'value': region
            })

        for city in cities:
            if query in city.lower():
                results.append({
                    'type': 'city',
                    'name': city,
                    'value': city,
                    'region': region,
                    'parent': region
                })

    # Сортировка
    results.sort(key=lambda x: (0 if x['name'].lower().startswith(query) else 1, x['name'].lower()))
    return results[:20]
