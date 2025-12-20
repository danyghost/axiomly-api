import joblib
import pandas as pd
import numpy as np
from catboost import CatBoostRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, mean_absolute_percentage_error
import warnings

warnings.filterwarnings('ignore')


# Загрузка данных
def load_data():
    data = pd.read_csv("real_estate.csv")
    return data


def preprocess_data(df):
    df = df.copy()
    print("Предобработка данных")

    # Обработка пропущенных значений
    df['building_type'] = df['building_type'].fillna(-1)
    df['object_type'] = df['object_type'].fillna(-1)
    df['rooms'] = df['rooms'].fillna(-1)
    df['area'] = df['area'].fillna(df['area'].median())
    df['kitchen_area'] = df['kitchen_area'].fillna(df['kitchen_area'].median())
    df['level'] = df['level'].fillna(df['level'].median())
    df['levels'] = df['levels'].fillna(df['levels'].median())

    # Защита от деления на ноль
    df['levels'] = df['levels'].replace(0, 1)

    # Этаж не может быть выше этажности дома
    df = df[df['level'] <= df['levels']]

    # Создание новых признаков
    df['room_size'] = df['area'] / df['rooms'].replace(-1, 0.5).clip(lower=0.5)
    df['floor_ratio'] = df['level'] / df['levels']
    df['price_per_sqm'] = df['price'] / df['area']

    # Обработка выбросов (убираем нижнюю и верхнюю границу по цене за м²)
    df = df[(df['price'] > 0) & (df['area'] > 10)]

    Q1 = df['price_per_sqm'].quantile(0.25)
    Q3 = df['price_per_sqm'].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    df = df[
        (df['price_per_sqm'] >= lower_bound) &
        (df['price_per_sqm'] <= upper_bound)
        ]
    print(f"Границы выбросов (м²): [{lower_bound:.2f}, {upper_bound:.2f}]")

    df = df[df["price"] >= 300_000]

    # Логарифмирование цены для нормализации распределения
    df['price_log'] = np.log1p(df['price'])

    # Убираем бесконечные значения
    for col in ['room_size', 'floor_ratio']:
        df[col] = df[col].replace([np.inf, -np.inf], df[col].median())
        df[col] = df[col].fillna(df[col].median())

    # Оптимизация типов данных для экономии памяти
    for col in df.select_dtypes(include=['int64']).columns:
        df[col] = df[col].astype('int32')
    for col in df.select_dtypes(include=['float64']).columns:
        df[col] = df[col].astype('float32')

    return df


def train_model():
    """Обучение модели"""
    data = load_data()
    df = preprocess_data(data)

    features = ['region_name', 'building_type', 'object_type', 'level', 'levels',
                'rooms', 'area', 'kitchen_area', 'room_size', 'floor_ratio']

    X = df[features]
    y = df['price_log']

    # Разделение данных
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0, shuffle=False)

    cat_features = ['region_name', 'building_type', 'object_type', 'rooms']

    for col in cat_features:
        X_train[col] = X_train[col].astype(str)
        X_test[col] = X_test[col].astype(str)

    model = CatBoostRegressor(
        cat_features=cat_features,
        iterations=200,
        learning_rate=0.1,
        depth=5,
        l2_leaf_reg=3,
        subsample=0.7,
        random_strength=1,
        verbose=50,
        thread_count=-1,
        early_stopping_rounds=30,
        loss_function='RMSE',
        custom_metric=['MAE'],
        task_type='CPU',
        bootstrap_type='Bernoulli',
        max_ctr_complexity=1,
        used_ram_limit='4gb',
        random_seed=0
    )

    print("Обучение модели")
    model.fit(
        X_train, y_train,
        eval_set=(X_test, y_test),
        use_best_model=True,
        verbose_eval=50,
        plot=False
    )

    # Прогноз
    pred_log = model.predict(X_test)

    # Переводим обратно из логарифма
    pred = np.expm1(pred_log)
    y_test_orig = np.expm1(y_test)

    # Метрики
    mae = mean_absolute_error(y_test_orig, pred)
    mse = mean_squared_error(y_test_orig, pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test_orig, pred)
    wape = (np.abs(y_test_orig - pred).sum() / (y_test_orig.sum() + 1e-9)) * 100

    print("Результаты\n")
    print(f"MAE: {mae:,.0f} руб.")
    print(f"MSE: {mse:,.0f}")
    print(f"RMSE: {rmse:,.0f} руб.")
    print(f"R²: {r2:.4f}")
    print(f"WAPE: {wape:.2f}%")
    print(f"Средняя цена в тестовой выборке: {y_test_orig.mean():,.0f} руб.")
    print(f"Отношение MAE к средней цене: {mae / y_test_orig.mean():.3f}")

    # Сохранение модели
    joblib.dump({'model': model}, 'models/sale_model.joblib')
    print("Модель продажи сохранена")

    return model


if __name__ == "__main__":
    try:
        model = train_model()
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback

        traceback.print_exc()