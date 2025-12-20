import joblib
from pathlib import Path


class ModelRegistry:
    def __init__(self):
        self.models = {}
        self.encoders = {}

    @classmethod
    def load_from_disk(cls, models_dir: str):
        """Загружает модели из папки при старте приложения"""
        registry = cls()
        models_path = Path(models_dir)

        # Загружаем модель продажи
        sale_path = models_path / "sale_model.joblib"
        if sale_path.exists():
            data = joblib.load(sale_path)
            registry.models['sale'] = data['model']
            print("✓ Модель продажи загружена")
        else:
            print("✗ Модель продажи не найдена")

        # Загружаем модель аренды
        rent_path = models_path / "rent_model.joblib"
        if rent_path.exists():
            data = joblib.load(rent_path)
            registry.models['rent'] = data['model']
            print("✓ Модель аренды загружена")
        else:
            print("✗ Модель аренды не найдена")

        return registry

    def get(self, deal_type: str):
        """Возвращает модель для типа сделки"""
        model = self.models.get(deal_type)
        return model
