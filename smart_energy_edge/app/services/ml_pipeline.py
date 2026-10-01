import os
import glob
import sqlite3
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Tuple
import pandas as pd
import lightgbm as lgb
import joblib
from sklearn.metrics import mean_absolute_error, mean_squared_error
from influxdb_client import InfluxDBClient
from app.core.config import DB_PATH, MODELS_DIR, EVALUATION_WINDOW_HOURS
from app.db.database import INFLUX_URL, INFLUX_TOKEN, INFLUX_ORG, INFLUX_BUCKET

logger = logging.getLogger(__name__)

# Глобальний кеш для утримання моделі в оперативній пам'яті (уникаємо I/O операцій на кожен запит)
_active_model = None
_active_model_version: Optional[str] = None


def load_active_model() -> None:
    """Шукає найсвіжішу модель на диску і завантажує її в оперативну пам'ять."""
    global _active_model, _active_model_version
    try:
        models = glob.glob(os.path.join(MODELS_DIR, "lgb_model_v*.pkl"))
        if not models:
            logger.warning("Моделі не знайдено. Потрібно запустити навчання (train_model).")
            return
            
        latest_model_path = max(models, key=os.path.getctime)
        _active_model = joblib.load(latest_model_path)
        _active_model_version = os.path.basename(latest_model_path).replace('.pkl', '')
        
        logger.info("Успішно завантажено модель %s в оперативну пам'ять.", _active_model_version)
    except Exception as e:
        logger.error("Помилка при завантаженні моделі в пам'ять: %s", e, exc_info=True)


def fetch_from_central_db() -> bool:
    """Спроба завантажити історію з хмари, якщо локальна БД порожня."""
    logger.warning("Локальних даних немає. Спроба підключення до Центральної БД (Cloud)...")
    logger.warning("Центральна БД поки недоступна (MVP версія).")
    return False


def query_influx_to_df(query: str) -> pd.DataFrame:
    """Виконує безпечний Flux-запит до InfluxDB і повертає Pandas DataFrame."""
    try:
        # Використання контекстного менеджера гарантує закриття з'єднання
        with InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG) as client:
            query_api = client.query_api()
            df = query_api.query_data_frame(query)
            
            # Якщо Influx повертає список датафреймів, конкатенуємо їх
            if isinstance(df, list):
                if not df:
                    return pd.DataFrame()
                df = pd.concat(df, ignore_index=True)
                
            if not df.empty and '_time' in df.columns:
                df = df.rename(columns={'_time': 'timestamp'})
                # Видалення часових зон для уникнення конфліктів у Pandas
                df['timestamp'] = df['timestamp'].dt.tz_localize(None) 
                
            return df
    except Exception as e:
        logger.error("Помилка читання з InfluxDB: %s", e)
        return pd.DataFrame()


def train_model() -> bool:
    """Тренує модель на історичних даних, версіонує її та оновлює кеш."""
    logger.info("Запуск процесу навчання (Train Pipeline)...")
    
    try:
        telemetry_query = f'''
            from(bucket: "{INFLUX_BUCKET}")
              |> range(start: -30d)
              |> filter(fn: (r) => r._measurement == "sensor_telemetry")
              |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
              |> keep(columns: ["_time", "solar_v", "solar_a"])
        '''
        df_telemetry = query_influx_to_df(telemetry_query)
        
        weather_query = f'''
            from(bucket: "{INFLUX_BUCKET}")
              |> range(start: -30d)
              |> filter(fn: (r) => r._measurement == "weather" and r.type == "historical")
              |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        '''
        df_weather = query_influx_to_df(weather_query)

        if len(df_telemetry) < 50 or len(df_weather) < 50:
            logger.warning("Недостатньо локальних даних для навчання.")
            if not fetch_from_central_db():
                return False 
            
        if df_telemetry.empty or df_weather.empty:
            logger.warning("Історичні дані для формування датасету відсутні.")
            return False

        # Формування цільової змінної
        df_telemetry['pzem_power_w'] = df_telemetry['solar_v'] * df_telemetry['solar_a']

        df_merged = pd.merge_asof(
            df_telemetry.sort_values('timestamp'), 
            df_weather.sort_values('timestamp'), 
            on='timestamp', 
            direction='backward'
        )
        
        df_merged['hour'] = df_merged['timestamp'].dt.hour
        features = ['hour', 'temp_c', 'cloud_cover_pct', 'solar_rad_w_m2']
        
        X = df_merged[features].fillna(0)
        y = df_merged['pzem_power_w']
        
        # Навчання алгоритму градієнтного бустингу
        model = lgb.LGBMRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)
        
        version = datetime.now().strftime("%Y%m%d_%H%M")
        model_name = f"lgb_model_v{version}.pkl"
        
        os.makedirs(MODELS_DIR, exist_ok=True)
        model_path = os.path.join(MODELS_DIR, model_name)
        
        joblib.dump(model, model_path)
        logger.info("Модель успішно навчена та збережена як %s!", model_name)
        
        # Гаряче оновлення моделі в оперативній пам'яті без рестарту сервера
        load_active_model()
        return True
    
    except Exception as e:
        logger.error("Помилка під час навчання моделі: %s", e, exc_info=True)
        return False


def evaluate_models() -> None:
    """Аналізує прогнози за минулу добу (MLOps: Model Drift Detection)."""
    logger.info("Запуск MLOps: Оцінка точності моделей...")
    
    try:    
        preds_query = f'''
            from(bucket: "{INFLUX_BUCKET}")
              |> range(start: -{EVALUATION_WINDOW_HOURS}h)
              |> filter(fn: (r) => r._measurement == "predictions")
              |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        '''
        df_preds = query_influx_to_df(preds_query)
        
        actual_query = f'''
            from(bucket: "{INFLUX_BUCKET}")
              |> range(start: -{EVALUATION_WINDOW_HOURS}h)
              |> filter(fn: (r) => r._measurement == "sensor_telemetry")
              |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        '''
        df_actual = query_influx_to_df(actual_query)

        if df_preds.empty or df_actual.empty:
            logger.info("Немає даних для оцінки (система акумулює дані).")
            return

        df_actual['pzem_power_w'] = df_actual['solar_v'] * df_actual['solar_a']

        df_merged = pd.merge_asof(
            df_preds.sort_values('timestamp'), 
            df_actual.sort_values('timestamp'), 
            on='timestamp', 
            direction='nearest',
            tolerance=pd.Timedelta('30min')
        ).dropna(subset=['pzem_power_w', 'predicted_power_w'])

        if df_merged.empty:
            logger.info("Не вдалося зіставити прогнози з реальністю (відсутні перетини у часі).")
            return

        models_tested = df_merged['model_version'].unique()
        
        # Безпечне підключення до реляційної бази для логування метрик
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            for model_ver in models_tested:
                df_model = df_merged[df_merged['model_version'] == model_ver]
                
                mae = mean_absolute_error(df_model['pzem_power_w'], df_model['predicted_power_w'])
                mse = mean_squared_error(df_model['pzem_power_w'], df_model['predicted_power_w'])
                
                cursor.execute("""
                    INSERT INTO model_evaluations (model_version, mae_score, mse_score)
                    VALUES (?, ?, ?)
                """, (model_ver, mae, mse))
                
                logger.info("📊 Модель %s перевірена. MAE: %.2f Вт.", model_ver, mae)
                
                # Автоматична ізоляція (видалення) деградованих моделей
                if mae > 500:
                    logger.warning("🚨 УВАГА! Модель %s деградувала. Ініційовано видалення...", model_ver)
                    bad_model_path = os.path.join(MODELS_DIR, f"{model_ver}.pkl")
                    if os.path.exists(bad_model_path):
                        os.remove(bad_model_path)
                        logger.info("🗑 Файл моделі %s видалено.", model_ver)
                        
                        # Якщо ми видалили поточну активну модель, потрібно перемкнутися на попередню
                        if _active_model_version == model_ver:
                            load_active_model()

            conn.commit()
    except Exception as e:
        logger.error("Помилка під час оцінки (MLOps): %s", e, exc_info=True)


def make_prediction() -> Optional[List[Tuple[int, float, str]]]:
    """Генерує прогноз на основі майбутньої погоди за допомогою закешованої моделі."""
    logger.info("Генерація прогнозу...")
    
    global _active_model, _active_model_version
    
    if _active_model is None:
        logger.warning("Активна модель відсутня в пам'яті. Відміна прогнозування.")
        return None
        
    try:
        dynamic_stop_time = (datetime.now(timezone.utc) + timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        future_weather_query = f'''
            from(bucket: "{INFLUX_BUCKET}")
              |> range(start: now(), stop: {dynamic_stop_time})
              |> filter(fn: (r) => r._measurement == "weather" and r.type == "future")
              |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        '''
        df_future = query_influx_to_df(future_weather_query)
        
        if df_future.empty:
            logger.warning("У базі InfluxDB немає прогнозу погоди на майбутнє.")
            return None
            
        df_future['hour'] = df_future['timestamp'].dt.hour
        features = ['hour', 'temp_c', 'cloud_cover_pct', 'solar_rad_w_m2']

        X_future = df_future[features].fillna(0)
        
        # Миттєвий предикт з оперативної пам'яті
        predictions = _active_model.predict(X_future)

        results = []
        for timestamp_val, pred_val in zip(df_future['timestamp'], predictions):
            target_unix = int(timestamp_val.timestamp())
            results.append((target_unix, float(pred_val), _active_model_version))
            
        return results
    
    except Exception as e:
        logger.error("Помилка генерації прогнозу: %s", e, exc_info=True)
        return None

# Ініціалізуємо модель у пам'яті при старті мікросервісу
load_active_model()