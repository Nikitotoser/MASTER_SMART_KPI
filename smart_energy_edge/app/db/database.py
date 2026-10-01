import logging
import sqlite3
import os
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from app.core.config import INFLUX_URL, INFLUX_TOKEN, INFLUX_ORG, INFLUX_BUCKET, DB_PATH
from app.models import IncomingTelemetry

# Ініціалізація логера
logger = logging.getLogger(__name__)

# Ініціалізація клієнта InfluxDB
influx_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = influx_client.write_api(write_options=SYNCHRONOUS)


def init_db():
    """Ініціалізація локальної SQLite бази для логування метаданих ML-моделей (MLOps)."""
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        
        # Використання контекстного менеджера гарантує безпечне закриття з'єднання
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_version TEXT,
                    evaluation_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    mae_score REAL,
                    mse_score REAL
                )
            """)
            conn.commit()
        logger.info("SQLite (MLOps) успішно ініціалізовано: %s", DB_PATH)
    except Exception as e:
        logger.error("Критична помилка ініціалізації SQLite: %s", e)


def save_telemetry(data: IncomingTelemetry) -> bool:
    """Збереження валідованої телеметрії від ESP32 в InfluxDB."""
    try:
        point = (
            Point("sensor_telemetry")
            .tag("device", "esp32")
            .field("solar_v", data.solar.voltage)
            .field("solar_a", data.solar.current)
            .field("bat_v", data.battery.voltage)
            .field("bat_a", data.battery.current)
            .time(data.timestamp, WritePrecision.S)
        )
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
        return True
    except Exception as e:
        logger.error("Помилка запису телеметрії в InfluxDB: %s", e)
        return False


def save_weather(timestamp_unix: int, temp: float, cloud: float, solar: float) -> bool:
    """Збереження історичної фактичної погоди."""
    try:
        point = (
            Point("weather")
            .tag("type", "historical")
            .field("temp_c", float(temp))
            .field("cloud_cover_pct", float(cloud))
            .field("solar_rad_w_m2", float(solar))
            .time(timestamp_unix, WritePrecision.S)
        )
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
        return True
    except Exception as e:
        logger.error("Помилка запису історичної погоди: %s", e)
        return False


def save_future_weather(target_timestamp_unix: int, temp: float, cloud: float, solar: float) -> bool:
    """Збереження прогнозу погоди на майбутнє."""
    try:
        point = (
            Point("weather")
            .tag("type", "future")
            .field("temp_c", float(temp))
            .field("cloud_cover_pct", float(cloud))
            .field("solar_rad_w_m2", float(solar))
            .time(target_timestamp_unix, WritePrecision.S)
        )
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
        return True
    except Exception as e:
        logger.error("Помилка запису майбутньої погоди: %s", e)
        return False


def save_prediction(target_timestamp_unix: int, predicted_w: float, model_ver: str) -> bool:
    """Збереження прогнозу енергоспоживання від ML-моделі."""
    try:
        point = (
            Point("predictions")
            .tag("model_version", model_ver)
            .field("predicted_power_w", float(predicted_w))
            .time(target_timestamp_unix, WritePrecision.S)
        )
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
        return True
    except Exception as e:
        logger.error("Помилка запису прогнозу ML-моделі: %s", e)
        return False