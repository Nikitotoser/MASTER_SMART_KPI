import threading
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Чисті імпорти відносно кореневої директорії проєкту
from app.core.config import API_HOST, API_PORT
from app.services.mqtt_service import start_mqtt
from app.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ініціалізація фонових процесів (MQTT) при старті сервера."""
    threading.Thread(target=start_mqtt, daemon=True).start()
    yield


app = FastAPI(title="Smart Energy API", lifespan=lifespan)

# Налаштування CORS для взаємодії з React-фронтендом
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Реєстрація модулів маршрутизації
app.include_router(router)


@app.get("/")
def root() -> dict[str, str]:
    """Перевірка статусу працездатності API (Healthcheck)."""
    return {
        "status": "ok", 
        "message": "Smart Energy Backend is running. Frontend is served separately."
    }


if __name__ == "__main__":
    # Запуск сервера
    uvicorn.run("app.main:app", host=API_HOST, port=API_PORT, reload=True)