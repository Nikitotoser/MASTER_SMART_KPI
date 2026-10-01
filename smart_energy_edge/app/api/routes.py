import os
import sqlite3
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter
from influxdb_client import InfluxDBClient

from app.core.config import DB_PATH, LOGS_DIR, INFLUX_URL, INFLUX_TOKEN, INFLUX_ORG, INFLUX_BUCKET
from app.core.logger import logger

# 1. Роутер для клієнтського API (Використовується React-фронтендом)
api_router = APIRouter()

# 2. Роутер для системного UI (Наразі не використовується, залишено для масштабування)
ui_router = APIRouter()


# ==========================================
# ПУБЛІЧНЕ API (Для Фронтенду)
# ==========================================

@api_router.get("/status", tags=["Client API"], summary="Перевірка статусу бекенду")
def read_root() -> dict[str, str]:
    """Перевірка статусу доступності системи (Healthcheck)."""
    logger.info("Отримано запит на перевірку статусу системи (/)")
    return {"status": "Онлайн", "project": "SmartEnergy Edge MVP"}


@api_router.get("/predictions/latest", tags=["Client API"], summary="Отримати прогноз споживання на 24 години")
def get_latest_predictions() -> dict:
    """Отримати актуальний прогноз на майбутні 24 години для рендерингу графіка (з InfluxDB)."""
    try:
        # Безпечне підключення до бази даних
        with InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG) as client:
            query_api = client.query_api()
            
            # Встановлюємо динамічний час зупинки (24 години від поточного моменту в UTC)
            now_utc = datetime.now(timezone.utc)
            dynamic_stop_time = (now_utc + timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%SZ')
            
            # Flux-запит: агрегуємо прогнози погодинно (mean)
            query = f'''
                from(bucket: "{INFLUX_BUCKET}")
                  |> range(start: now(), stop: {dynamic_stop_time})
                  |> filter(fn: (r) => r._measurement == "predictions")
                  |> filter(fn: (r) => r._field == "predicted_power_w")
                  |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
            '''
            
            tables = query_api.query(query, org=INFLUX_ORG)
            
            times = []
            powers = []
            
            for table in tables:
                for record in table.records:
                    dt = record.get_time()
                    times.append(int(dt.timestamp()))
                    powers.append(round(record.get_value(), 1))
                    
            return {"times": times, "powers": powers}
    except Exception as e:
        logger.error("Помилка отримання прогнозів: %s", e)
        return {"error": str(e)}


@api_router.get("/model/metrics", tags=["Client API"], summary="Отримати метрики останньої моделі")
def get_model_metrics() -> dict:
    """Отримує реальні дані якості моделі (MLOps)."""
    try:
        # Безпечне підключення за допомогою контекстного менеджера
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Дістаємо найсвіжіший запис оцінки моделі
            cursor.execute("SELECT model_version, mae_score, mse_score FROM model_evaluations ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            
        if row:
            return {
                "version": row[0],
                "mae": round(row[1], 2),
                "mse": round(row[2], 2)
            }
            
        # Якщо оцінок ще немає наприклад, під час першого запуску
        return {"version": "Очікує оцінки", "mae": 0, "mse": 0}
    except Exception as e:
        logger.error("Помилка отримання метрик: %s", e)
        return {"error": str(e)}


# ==========================================
# ПРИВАТНЕ API (Сховане з відкритої документації)
# ==========================================

@api_router.get("/stats", include_in_schema=False)
def get_system_stats() -> dict:
    """Отримати статистику наповненості Бази Даних (InfluxDB + SQLite)."""
    try:
        with InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG) as client:
            query_api = client.query_api()
            
            def get_influx_count(measurement: str, time_range: str = "-30d") -> int:
                query = f'''
                    from(bucket: "{INFLUX_BUCKET}")
                      |> range(start: {time_range})
                      |> filter(fn: (r) => r._measurement == "{measurement}")
                      |> count()
                '''
                result = query_api.query(query, org=INFLUX_ORG)
                for table in result:
                    for record in table.records:
                        return record.get_value()
                return 0

            telemetry = get_influx_count("sensor_telemetry")
            weather = get_influx_count("weather")
            predictions = get_influx_count("predictions", time_range="-30d")
            
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            try:
                last_mae = cursor.execute("SELECT mae_score FROM model_evaluations ORDER BY id DESC LIMIT 1").fetchone()[0]
                last_mae = round(last_mae, 2)
            except (TypeError, sqlite3.OperationalError):
                last_mae = "Ще не оцінено"
                
        return {
            "telemetry_rows": telemetry,
            "weather_rows": weather,
            "predictions_rows": predictions,
            "last_model_mae": last_mae
        }
    except Exception as e:
        logger.error("Помилка отримання статистики: %s", e)
        return {"error": str(e)}


@api_router.get("/logs", include_in_schema=False)
def get_recent_logs(lines: int = 20) -> dict:
    """Отримати останні рядки системного логу."""
    try:
        log_files = [os.path.join(LOGS_DIR, f) for f in os.listdir(LOGS_DIR) if f.endswith('.log')]
        if not log_files:
            return {"logs": ["Лог файли не знайдені."]}
            
        latest_log = max(log_files, key=os.path.getctime)
        
        with open(latest_log, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
            return {"logs": all_lines[-lines:]}
    except Exception as e:
        return {"error": str(e)}