from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
def health(request: Request):
    """Проверка работоспособности"""
    models = request.app.state.models
    city_mapper = request.app.state.city_mapper

    return {
        'status': 'ok',
        'sale_model_loaded': 'sale' in models.models,
        'rent_model_loaded': 'rent' in models.models,
        'regions_count': len(city_mapper.region_to_cities),
        'message': 'Сервер работает'
    }
