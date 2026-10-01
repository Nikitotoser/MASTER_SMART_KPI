from fastapi import APIRouter, Query

from app.db.database import get_recent_telemetry
from app.db.models import TelemetryResponse

# Групування ендпоінтів з префіксом версіювання
router = APIRouter(prefix="/api/v1", tags=["Telemetry"])


@router.get("/status", response_model=dict[str, str])
def get_status():
    """Перевірка статусу доступності маршрутизатора API (Healthcheck)."""
    return {"status": "ok", "message": "Backend is running"}


@router.get("/telemetry/latest", response_model=list[TelemetryResponse])
def get_telemetry(
    limit: int = Query(
        default=10, 
        description="Кількість останніх записів для відображення", 
        ge=1, 
        le=500
    )
):
    """
    Отримання останніх агрегованих даних телеметрії.
    Використовується фронтендом для рендерингу графіків у реальному часі.
    """
    data = get_recent_telemetry()
    return data[:limit]