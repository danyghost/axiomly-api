import pandas as pd
import numpy as np
# import seaborn as sns
import matplotlib.pyplot as plt


# ----- Загрузка данных -----
data = pd.read_csv('real_estate.csv')



# ----- Первичное знакомство с данными -----

print(data.info())
print(data.describe())
print(data.shape)
print(data.isnull().sum())



# ----- Выявление пропущенных значений -----

# # Подсчет пропущенных значений
# total_count = data.shape[0]
#
# num_cols = []
# for col in data.columns:
#     null_count = data[data[col].isnull()].shape[0]
#     dt = data[col].dtype
#     if null_count > 0 and (dt == 'int64' or dt == 'float64'):
#         num_cols.append(col)
#         null_perc = round((null_count / total_count) * 100.0, 2)
#         print(f"Столбец {col}. Тип данных {dt}. Количество пропущенных значений {null_count}, {null_perc}%")
#     elif null_count == 0:
#         print("Пропущенных числовых значений нет")
#         break
#
# cat_cols = []
# for col in data.columns:
#     null_count = data[data[col].isnull()].shape[0]
#     dt = data[col].dtype
#     if null_count > 0 and (dt == 'object'):
#         cat_cols.append(col)
#         null_perc = round((null_count / total_count) * 100.0, 2)
#         print(f"Столбец {col}. Тип данных {dt}. Количество пропущенных значений {null_count}, {null_perc}%")
#     elif null_count == 0:
#         print("Пропущенных категориальных значений нет")
#         break



# ----- Проверка на наличие дубликатов -----

# def data_sanity_check(df):
#     checks = {
#         'total_rows': len(df),
#         'exact_duplicates': df.duplicated().sum(),
#         'missing_values': df.isnull().sum().sum()
#     }
#
#     print("Проверка данных на дубликаты:")
#     for check, value in checks.items():
#         print(f"   {check}: {value}")
#
#     # Решение по дубликатам
#     dup_ratio = checks['exact_duplicates'] / checks['total_rows']
#     if dup_ratio > 0.1:
#         print("Много дубликатов (>10%)!")
#     elif dup_ratio > 0.01:
#         print(f"Есть дубликаты, их {dup_ratio * 100}%!")
#     else:
#         print("Дубликатов мало")
#
# # Запускаем в начале работы с любым новым датасетом
# data_sanity_check(data)




# ----- Выявление и удаление выбросов -----

# plt.figure(figsize=(15,5))
#
# plt.subplot(1, 2, 1) # Система координат для графиков, в нашем случае (1 строка, 2 столбца и позиция 1)
# sns.violinplot(x=np.log10(data[data['price'] > 0]['price']))
# plt.title('Данные до очистки: Стоимость квартир')
# plt.xlabel('log10(Цена)')
#
#
# data_clean = data.copy()
# data_clean = data_clean[data_clean['price'] > 0]
# data_clean['log_price'] = np.log10(data_clean['price'])
#
# Q1_log = data_clean['log_price'].quantile(0.25)
# Q3_log = data_clean['log_price'].quantile(0.75)
# IQR_log = Q3_log - Q1_log
# lower_bound_log = Q1_log - 1.5 * IQR_log
# upper_bound_log = Q3_log + 1.5 * IQR_log
#
# data_clean = data_clean[
#     (data_clean['log_price'] >= lower_bound_log) &
#     (data_clean['log_price'] <= upper_bound_log)
# ]
#
# lower_bound = 10**lower_bound_log
# upper_bound = 10**upper_bound_log
#
# print(f"Границы в логарифмированной шкале: [{lower_bound_log:.2f}, {upper_bound_log:.2f}]")
# print(f"Границы в рублях: [{10**lower_bound_log:,.0f}, {10**upper_bound_log:,.0f}]")
#
# plt.subplot(1, 2, 2)
# sns.violinplot(x=data_clean['log_price'])
# plt.title('Данные после очистки: Стоимость квартир')
# plt.xlabel('log10(Цена)')
#
# plt.tight_layout() # Автоматическая настройка параметров подграфиков
# plt.show()
#
# print(f"Удалено записей: {len(data) - len(data_clean)}")




# # Сначала считаем частоты
# value_counts = data['region_name'].value_counts()
# # value_counts = value_counts[value_counts > 100000]
# print(value_counts)
#
# # Строим барплот
# plt.figure(figsize=(20, 5))
# sns.barplot(x=value_counts.index, y=value_counts.values)
# plt.title('Распределение квартир по количеству городов')
# plt.xlabel('Регионы')
# plt.ylabel('Количество квартир')
# plt.xticks(rotation=90)
# plt.show()