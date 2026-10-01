import os
from typing import Final

# 1. Шляхи (Автоматичне визначення кореня проєкту)
BASE_DIR: Final[str] = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR: Final[str] = os.path.join(BASE_DIR, "data")
LOGS_DIR: Final[str] = os.path.join(BASE_DIR, "logs")
MODELS_DIR: Final[str] = os.path.join(BASE_DIR, "models")

# Створюємо папки, якщо їх немає
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

# 2. База даних (SQLite для MLOps)
DB_PATH: Final[str] = os.path.join(DATA_DIR, "smart_lab.db")

# 3. База даних (InfluxDB)
INFLUX_URL: Final[str] = os.getenv("INFLUX_URL", "http://localhost:8086")
INFLUX_TOKEN: Final[str] = os.getenv("INFLUX_TOKEN", "secretpassword_smartenergy6")
INFLUX_ORG: Final[str] = os.getenv("INFLUX_ORG", "KPI")
INFLUX_BUCKET: Final[str] = os.getenv("INFLUX_BUCKET", "smart_energy")

# 4. Гео-координати
LAT: Final[float] = float(os.getenv("LAT", "50.45"))
LON: Final[float] = float(os.getenv("LON", "30.46"))

# 5. MQTT Налаштування
MQTT_BROKER: Final[str] = os.getenv("MQTT_BROKER", "broker.hivemq.com")
MQTT_PORT: Final[int] = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC: Final[str] = os.getenv("MQTT_TOPIC", "smart_energy/telemetry")

# 6. Режим роботи та інтервали
TEST_MODE: Final[bool] = os.getenv("TEST_MODE", "False").lower() in ("true", "1", "yes")

if TEST_MODE:
    # Швидкі налаштування для розробки (Dev/Test)
    INTERVAL_WEATHER_MIN: Final[int] = 1       # Поточна погода (кожну хвилину)
    INTERVAL_FUTURE_MIN: Final[int] = 2        # Прогноз на завтра (кожні 2 хв)
    INTERVAL_PREDICTION_MIN: Final[int] = 3    # Генерація ML-прогнозу (кожні 3 хв)
    INTERVAL_BACKFILL_MIN: Final[int] = 5      # Пошук пропусків (кожні 5 хв)
    INTERVAL_EVALUATION_MIN: Final[int] = 4    # MLOps оцінка моделей (кожні 4 хв)
    EVALUATION_WINDOW_HOURS: Final[int] = 1    # Вікно оцінки: остання 1 година
else:
    # Реальні налаштування для Production 
    INTERVAL_WEATHER_MIN: Final[int] = 60      # Поточна погода (раз на годину)
    INTERVAL_FUTURE_MIN: Final[int] = 360      # Оновлення прогнозу (раз на 6 годин)
    INTERVAL_PREDICTION_MIN: Final[int] = 60   # Генерація ML-прогнозу (щогодини)
    INTERVAL_BACKFILL_MIN: Final[int] = 720    # Пошук пропусків (двічі на добу)
    INTERVAL_EVALUATION_MIN: Final[int] = 1440 # MLOps оцінка моделей (раз на добу)
    EVALUATION_WINDOW_HOURS: Final[int] = 24   # Вікно оцінки: останні 24 години