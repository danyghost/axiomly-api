from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd

from core.parsers.analogs_provider import get_analogs

SALE_FEATURES = [
    'region_name', 'building_type', 'object_type', 'level', 'levels',
    'rooms', 'area', 'kitchen_area', 'room_size', 'floor_ratio'
]

RENT_FEATURES = [
    'type', 'gas', 'area', 'rooms', 'kitchen_area', 'build_year', 'material',
    'build_series_category', 'level', 'levels', 'rubbish_chute', 'build_overlap',
    'build_walls', 'heating', 'city', 'floor_ratio', 'is_new_building'
]

def filter_outliers_iqr(prices: List[float]) -> List[float]:
    if len(prices) < 3:
        return prices
    arr = np.array(prices)
    q1 = np.percentile(arr, 25)
    q3 = np.percentile(arr, 75)
    iqr = q3 - q1
    return arr[(arr >= q1 - 1.5 * iqr) & (arr <= q3 + 1.5 * iqr)].tolist()

def prepare_sale_input(input_data: Dict[str, Any]) -> pd.DataFrame:
    d = dict(input_data)

    d['region_name'] = str(d.get('region', 'unknown'))
    d['building_type'] = str(d.get('building_type', 'unknown'))
    d['object_type'] = str(d.get('object_type', 'unknown'))
    d['rooms'] = str(d.get('rooms', 'unknown'))
    rooms_num = float(d.get('rooms', 1))
    area = float(d.get('area', 50))
    level = float(d.get('level', 1))
    levels = max(float(d.get('levels', 5)), 1.0)

    d['room_size'] = area / (0.5 if rooms_num == 0 else max(rooms_num, 0.5))
    d['floor_ratio'] = level / levels

    X = pd.DataFrame([{k: d.get(k, 0) for k in SALE_FEATURES}])

    # Признаки должны быть строками
    for col in ['region_name', 'building_type', 'object_type', 'rooms']:
        X[col] = X[col].astype(str)

    return X

def prepare_rent_input(input_data: Dict[str, Any]) -> pd.DataFrame:
    d = dict(input_data)

    building_type_mapping = {'0':'unknown','1':'panel','2':'monolithic','3':'brick','4':'block','5':'wood'}
    object_type_mapping = {'1':'secondary','2':'new'}

    building_type = str(d.get('building_type', '0'))
    object_type = str(d.get('object_type', '1'))

    d['material'] = building_type_mapping.get(building_type, 'unknown')
    d['type'] = object_type_mapping.get(object_type, 'secondary')

    d['gas'] = 'unknown'
    d['build_year'] = 2000 if object_type == '2' else 1990
    d['build_series_category'] = 'unknown'
    d['rubbish_chute'] = 'unknown'
    d['build_overlap'] = 'unknown'
    d['build_walls'] = 'unknown'
    d['heating'] = 'unknown'
    d['city'] = d.get('city', 'unknown')

    level = float(d.get('level', 1))
    levels = max(float(d.get('levels', 5)), 1.0)
    d['floor_ratio'] = 0.5 if not np.isfinite(level / levels) else (level / levels)
    d['is_new_building'] = object_type == '2'

    row = {}
    for k in RENT_FEATURES:
        if k in ['type','gas','material','build_series_category','rubbish_chute','build_overlap','build_walls','heating','city']:
            row[k] = str(d.get(k, 'unknown'))
        else:
            row[k] = float(d.get(k, 0) or 0)
    return pd.DataFrame([row])

def predict_with_analogs(
    input_data: Dict[str, Any],
    deal_type: str,
    model
) -> Tuple[float, float, List[Dict[str, Any]]]:

    if deal_type == 'sale':
        X = prepare_sale_input(input_data)
        ml_price = float(model.predict(X)[0])
    else:
        X = prepare_rent_input(input_data)
        ml_price = float(np.expm1(model.predict(X)[0]))

    analogs = get_analogs(
        city=input_data['city'],
        deal_type=deal_type,
        rooms=int(input_data['rooms']),
        area=float(input_data['area']),
    )

    final_price = ml_price
    if analogs:
        prices = []
        for a in analogs:
            p = a.get("price")
            if p is None:
                continue
            p = float(p)
            if deal_type == 'rent' and 8000 <= p <= 500000:
                prices.append(p)
            if deal_type == 'sale' and 1000000 <= p <= 50000000:
                prices.append(p)

        prices = filter_outliers_iqr(prices)
        if prices:
            cian_med = float(np.median(prices))
            w_ml, w_analog = (0.3, 0.7) if deal_type == 'rent' else (0.2, 0.8)
            final_price = ml_price * w_ml + cian_med * w_analog

    return float(final_price), float(ml_price), analogs