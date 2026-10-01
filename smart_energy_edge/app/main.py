from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from app.core.logger import logger
from app.core.config import (
    INTERVAL_WEATHER_MIN, 
    INTERVAL_FUTURE_MIN, 
    INTERVAL_PREDICTION_MIN, 
    INTERVAL_BACKFILL_MIN,
    TEST_MODE,
    INTERVAL_EVALUATION_MIN
)
from app.db.database import init_db, save_prediction
from app.services.weather import fetch_and_save_weather, fetch_future_weather
from app.services.mqtt_client import start_mqtt
from app.services.ml_pipeline import train_model, make_prediction, evaluate_models
from app.services.backfill_weather import run_backfill
from app.api.routes import api_router, ui_router

# Ініціалізація планувальника фонових задач
scheduler = BackgroundScheduler()


# ==========================================
# ФОНОВІ ЗАДАЧІ (CRON JOBS)
# ==========================================

def prediction_job() -> None:
    """Регулярна генерація прогнозів енергоспоживання."""
    logger.info("Запуск циклу прогнозування...")
    try:
        results = make_prediction() 
        
        if not results:
            logger.warning("Даних для прогнозу немає. Можливий запуск навчання...")
            if train_model():
                results = make_prediction()
                
        if results:
            for target_time, predicted_power, model_ver in results:
                save_prediction(target_time, predicted_power, model_ver)
                
            logger.info("Збережено %s точок прогнозу (Версія моделі: %s).", len(results), results[0][2])
    except Exception as e:
        logger.error("Помилка під час прогнозування: %s", e, exc_info=True)
        

def maintenance_job() -> None:
    """Регулярний пошук та заповнення пропусків в історії погоди."""
    logger.info("Запуск системної перевірки (Backfill)...")
    try:
        run_backfill()
    except Exception as e:
        logger.error("Помилка під час Backfill: %s", e, exc_info=True)


def weather_forecast_job() -> None:
    """Регулярне оновлення локального кешу прогнозу погоди."""
    logger.info("🌤 Оновлення локального кешу погоди на майбутнє...")
    try:
        fetch_future_weather()
    except Exception as e:
        logger.error("Помилка оновлення прогнозу погоди: %s", e, exc_info=True)


# ==========================================
# ЖИТТЄВИЙ ЦИКЛ ДОДАТКУ
# ==========================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ініціалізація ресурсів при старті та очищення при зупинці сервера."""
    logger.info("Ініціалізація запуску сервера...")
    try:
        init_db()
        mode = "ТЕСТОВИЙ (Швидкий)" if TEST_MODE else "ПРОДАКШЕН (Реальний)"
        logger.info("Базу даних ініціалізовано! Режим: %s", mode)
        
        # Запускаємо фонові сервіси та первинне завантаження даних
        start_mqtt()
        fetch_and_save_weather()
        fetch_future_weather()
        maintenance_job()
        
        # Налаштовуємо планувальник з misfire_grace_time (захист від пропуску задач)
        scheduler.add_job(fetch_and_save_weather, 'interval', minutes=INTERVAL_WEATHER_MIN, misfire_grace_time=60)
        scheduler.add_job(weather_forecast_job, 'interval', minutes=INTERVAL_FUTURE_MIN, misfire_grace_time=60)
        scheduler.add_job(prediction_job, 'interval', minutes=INTERVAL_PREDICTION_MIN, misfire_grace_time=60)
        scheduler.add_job(maintenance_job, 'interval', minutes=INTERVAL_BACKFILL_MIN, misfire_grace_time=60)
        scheduler.add_job(evaluate_models, 'interval', minutes=INTERVAL_EVALUATION_MIN, misfire_grace_time=60)
        
        scheduler.start()
        logger.info("⏱ Планувальник задач успішно запущено.")
    except Exception as e:
        logger.critical("КРИТИЧНА ПОМИЛКА під час запуску: %s", e, exc_info=True)
    
    yield
    
    scheduler.shutdown()
    logger.info("Сервер зупинено. Планувальник вимкнено.")


# ==========================================
# ІНІЦІАЛІЗАЦІЯ FASTAPI ТА ПІДКЛЮЧЕННЯ РОУТІВ
# ==========================================

app = FastAPI(
    title="⚡ Smart Energy Edge API",
    lifespan=lifespan,
    description=(
        "Публічний API для клієнтської частини (Frontend).\n\n"
        "Надає доступ до актуальних ML-прогнозів енергоспоживання лабораторії."
    ),
    version="1.0.0",
    contact={"name": "Гончаренко Микита ТВ-51МП (Backend & ML Engineer)"},
    openapi_tags=[{"name": "Client API", "description": "Методи для отримання даних на клієнтську частину"}]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Підключаємо винесені роути
app.include_router(api_router, prefix="/api")
app.include_router(ui_router)