import logging
from datetime import datetime, timezone
import requests
from influxdb_client import InfluxDBClient
from app.core.config import LAT, LON, INFLUX_URL, INFLUX_TOKEN, INFLUX_ORG, INFLUX_BUCKET
from app.db.database import save_weather

logger = logging.getLogger(__name__)


def get_missing_intervals() -> list[str]:
    """Знаходить дати, для яких є телеметрія, але немає погоди (запит до InfluxDB)."""
    try:
        # Контекстний менеджер для безпечного керування з'єднанням
        with InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG) as client:
            query_api = client.query_api()
            
            telemetry_query = f'''
                from(bucket: "{INFLUX_BUCKET}")
                  |> range(start: -30d)
                  |> filter(fn: (r) => r._measurement == "sensor_telemetry")
                  |> window(every: 1d)
                  |> count()
            '''
            
            weather_query = f'''
                from(bucket: "{INFLUX_BUCKET}")
                  |> range(start: -30d)
                  |> filter(fn: (r) => r._measurement == "weather" and r.type == "historical")
                  |> window(every: 1d)
                  |> count()
            '''

            telemetry_result = query_api.query(query=telemetry_query, org=INFLUX_ORG)
            weather_result = query_api.query(query=weather_query, org=INFLUX_ORG)
            
            telemetry_days = set()
            weather_days = set()

            for table in telemetry_result:
                for record in table.records:
                    telemetry_days.add(record.get_start().strftime('%Y-%m-%d'))
                    
            for table in weather_result:
                for record in table.records:
                    weather_days.add(record.get_start().strftime('%Y-%m-%d'))

            missing_days = list(telemetry_days - weather_days)
            missing_days.sort() 
            
            return missing_days
            
    except Exception as e:
        logger.error("Помилка InfluxDB при пошуку пропусків погоди: %s", e, exc_info=True)
        return []


def backfill_weather_for_day(day_str: str) -> None:
    """Завантажує історичну погоду за конкретний день і зберігає в InfluxDB."""
    logger.info("Завантаження історії погоди для: %s...", day_str)
    
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": LAT,
        "longitude": LON,
        "start_date": day_str,
        "end_date": day_str,
        "hourly": "temperature_2m,cloud_cover,shortwave_radiation"
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        hourly = data.get('hourly', {})
        times = hourly.get('time', [])
        temps = hourly.get('temperature_2m', [])
        clouds = hourly.get('cloud_cover', [])
        solar = hourly.get('shortwave_radiation', [])
        
        saved_count = 0
        for time_val, temp_val, cloud_val, solar_val in zip(times, temps, clouds, solar):
            dt_str = time_val.replace('T', ' ') + ":00"
            
            # Строге приведення до UTC для InfluxDB
            target_dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
            timestamp_unix = int(target_dt.timestamp())
            
            save_weather(timestamp_unix, temp_val, cloud_val, solar_val)
            saved_count += 1
            
        logger.info("Дані за %s успішно додано (%s записів).", day_str, saved_count)
        
    except requests.exceptions.RequestException as e:
        logger.error("Помилка мережі при завантаженні історії для %s: %s", day_str, e)
    except Exception as e:
        logger.error("Неочікувана помилка при завантаженні історії для %s: %s", day_str, e, exc_info=True)


def run_backfill() -> None:
    """Основний цикл заповнення пропусків."""
    logger.info("🔍 Пошук пропусків у даних погоди (за останні 30 днів)...")
    missing_days = get_missing_intervals()
    
    if not missing_days:
        logger.info("Пропусків не знайдено. База погоди в InfluxDB в нормі.")
        return

    logger.info("Знайдено днів без погоди: %s (%s)", len(missing_days), missing_days)
    for day in missing_days:
        backfill_weather_for_day(day)
    
    logger.info("Процес Backfill завершено.")


if __name__ == "__main__":
    run_backfill()