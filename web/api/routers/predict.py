from fastapi import APIRouter, Request, HTTPException
from web.api.schemas import PredictRequest, PredictResponse
from predict_price import predict_with_analogs

router = APIRouter()


@router.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest, request: Request):
    """Прогноз цены с аналогами"""
    models = request.app.state.models
    city_mapper = request.app.state.city_mapper

    # Получаем модель
    model = models.get(req.deal_type)
    if model is None:
        raise HTTPException(400, f"Модель {req.deal_type} не загружена")

    # Определяем город/регион
    location = req.location.strip()
    if location in city_mapper.region_to_cities:
        region = location
        cities = city_mapper.get_cities_by_region(region)
        if not cities:
            raise HTTPException(400, f"В регионе {region} нет городов")
        city = cities[0]
    else:
        city = location
        region = city_mapper.get_region_from_city(city)
        if region == "Неизвестный регион":
            raise HTTPException(400, f"Город {city} не найден")

    # Подготовка данных
    input_data = {
        'region': region,
        'city': city,
        'building_type': req.building_type,
        'object_type': req.object_type,
        'level': req.level,
        'levels': req.levels,
        'rooms': req.rooms,
        'area': req.area,
        'kitchen_area': req.kitchen_area or req.area * 0.2,
        'deal_type': req.deal_type
    }

    try:
        final_price, ml_price, analogs = predict_with_analogs(
            input_data=input_data, deal_type=req.deal_type, model=model
        )
    except Exception as e:
        raise HTTPException(500, str(e))

    # Форматируем ответ
    is_rent = req.deal_type == 'rent'
    price_suffix = "руб./мес" if is_rent else "руб."

    analogs_formatted = []
    for analog in analogs:
        analogs_formatted.append({
            'price': analog.get('price', 0),
            'price_formatted': f"{analog.get('price', 0):,.0f} {price_suffix}",
            'area': analog.get('area_total'),
            'rooms': analog.get('rooms'),
            'address': analog.get('address', ''),
            'url': analog.get('url', ''),
            'floor_info': analog.get('floor_info', '')
        })

    return {
        'success': True,
        'price': float(final_price),
        'price_formatted': f"{float(final_price):,.0f} {price_suffix}",
        'ml_price': float(ml_price),
        'ml_price_formatted': f"{float(ml_price):,.0f} {price_suffix}",
        'is_rent': is_rent,
        'price_suffix': price_suffix,
        'region': region,
        'city': city,
        'area': req.area,
        'rooms': req.rooms,
        'analogs_count': len(analogs),
        'analogs': analogs_formatted,
        'message': 'Прогноз выполнен'
    }
