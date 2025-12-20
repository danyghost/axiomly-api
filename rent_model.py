import joblib
import pandas as pd
import numpy as np
from catboost import CatBoostRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import warnings

warnings.filterwarnings('ignore')

# Загрузка данных
def load_data():
    data = pd.read_csv("rent_estate.csv")
    return data


def preprocess_data(df):
    df = df.copy()
    print("Предобработка данных")

    # Обработка выбросов в цене
    Q1 = df['price'].quantile(0.25)
    Q3 = df['price'].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    print(f"Границы выбросов: [{lower_bound:.2f}, {upper_bound:.2f}]")

    # Фильтрация выбросов
    initial_size = len(df)
    df = df[(df['price'] >= lower_bound) & (df['price'] <= upper_bound)]
    removed_outliers = initial_size - len(df)
    print(f"Удалено выбросов: {removed_outliers} ({removed_outliers / initial_size * 100:.1f}%)")

    # Логарифмирование цены для нормализации распределения
    df['price_log'] = np.log1p(df['price'])

    # Обработка пропущенных значений
    df['kitchen_area'] = df['kitchen_area'].fillna(df['kitchen_area'].median())
    df['living_area'] = df['living_area'].fillna(df['living_area'].median())
    df['build_year'] = df['build_year'].fillna(df['build_year'].median())

    # Новые признаки
    df['floor_ratio'] = df['level'] / df['levels']
    df['is_new_building'] = df['build_year'] > 2000

    # Обработка бесконечных значений
    df['floor_ratio'] = df['floor_ratio'].replace([np.inf, -np.inf], 0)

    # Замена NaN в категориальных признаках
    cat_cols = [
        'type', 'gas', 'material', 'build_series_category', 'rubbish_chute',
        'build_overlap', 'build_walls', 'heating', 'city'
    ]

    for col in cat_cols:
        df[col] = df[col].fillna('unknown')
        df[col] = df[col].astype(str)

    return df


def train_model():
    data = load_data()
    data_clean = preprocess_data(data)

    features = [
        'type', 'gas', 'area', 'rooms', 'kitchen_area', 'build_year', 'material',
        'build_series_category', 'level', 'levels','rubbish_chute', 'build_overlap',
        'build_walls', 'heating', 'city', 'floor_ratio', 'is_new_building'
    ]

    X = data_clean[features]
    y = data_clean['price_log']

    # Разделение данных
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)

    cat_cols = [
        'type', 'gas', 'material', 'build_series_category', 'rubbish_chute',
        'build_overlap', 'build_walls', 'heating', 'city'
    ]

    model = CatBoostRegressor(
        cat_features=cat_cols,
        n_estimators=2000,
        learning_rate=0.03,
        depth=8,
        l2_leaf_reg=3,
        random_state=0,
        verbose=100,
        early_stopping_rounds=100,
        loss_function='RMSE'
    )

    print("Обучение модели аренды")
    model.fit(
        X_train, y_train,
        eval_set=(X_test, y_test)
    )

    # Предсказания на тестовой выборке
    pred_log = model.predict(X_test)

    pred = np.expm1(pred_log)
    y_test_orig = np.expm1(y_test)

    # Оценка модели
    mae = mean_absolute_error(y_test_orig, pred)
    mse = mean_squared_error(y_test_orig, pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test_orig, pred)

    print("Результаты\n")
    print(f"MAE: {mae:.2f}")
    print(f"MSE: {mse:.2f}")
    print(f"RMSE: {rmse:.2f}")
    print(f"R²: {r2:.4f}")

    # Сохранение модели
    joblib.dump({'model': model}, 'models/rent_model.joblib')
    print("Модель аренды сохранена")

    return model


if __name__ == "__main__":
    try:
        model = train_model()
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback

        traceback.print_exc()