import logging
from datetime import datetime, timedelta, timezone
from typing import Final
import requests
from app.core.config import LAT, LON
from app.db.database import save_weather, save_future_weather

logger = logging.getLogger(__name__)

# Базовий URL для Open-Meteo
WEATHER_API_URL: Final[str] = "https://api.open-meteo.com/v1/forecast"


def fetch_and_save_weather() -> None:
    """Завантажує поточну погоду і зберігає в історичний лог (для навчання моделі)."""
    logger.info("Отримання поточної погоди...")
    
    params = {
        "latitude": LAT,
        "longitude": LON,
        "current": "temperature_2m,cloud_cover,shortwave_radiation",
        "timezone": "auto"
    }
    
    try:
        response = requests.get(WEATHER_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        current = data.get('current', {})
        temp = current.get('temperature_2m', 0.0)
        cloud = current.get('cloud_cover', 0.0)
        solar = current.get('shortwave_radiation', 0.0) 
        
        timestamp_unix = int(datetime.now(timezone.utc).timestamp())
        
        save_weather(timestamp_unix, temp, cloud, solar)
        logger.info("Поточну погоду збережено: %s°C, хмари %s%%, сонце %s W/m²", temp, cloud, solar)
        
    except requests.exceptions.RequestException as e:
        logger.error("Помилка мережі при отриманні поточної погоди: %s", e)
    except Exception as e:
        logger.error("Неочікувана помилка при обробці поточної погоди: %s", e, exc_info=True)


def fetch_future_weather() -> None:
    """Завантажує прогноз погоди на найближчі 24 години для генерації прогнозів."""
    logger.info("🌤 Завантаження прогнозу погоди на майбутнє...")
    
    params = {
        "latitude": LAT,
        "longitude": LON,
        "hourly": "temperature_2m,cloud_cover,shortwave_radiation",
        "forecast_days": 2, 
        "timezone": "auto"
    }
    
    try:
        response = requests.get(WEATHER_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        hourly = data.get('hourly', {})
        times = hourly.get('time', [])
        temps = hourly.get('temperature_2m', [])
        clouds = hourly.get('cloud_cover', [])
        solar = hourly.get('shortwave_radiation', [])
        
        now = datetime.now()
        end_time = now + timedelta(hours=24)
        
        saved_count = 0

        for time_val, temp_val, cloud_val, solar_val in zip(times, temps, clouds, solar):
            dt_str = time_val.replace('T', ' ') + ":00"
            target_dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
            
            if now <= target_dt <= end_time:
                target_timestamp_unix = int(target_dt.timestamp())
                
                save_future_weather(target_timestamp_unix, temp_val, cloud_val, solar_val)
                saved_count += 1
                
        logger.info("Прогноз погоди оновлено: кеш майбутнього заповнено (%s точок).", saved_count)
        
    except requests.exceptions.RequestException as e:
        logger.error("Помилка мережі при завантаженні прогнозу погоди на майбутнє: %s", e)
    except Exception as e:
        logger.error("Неочікувана помилка при обробці прогнозу погоди: %s", e, exc_info=True)