from fastapi import APIRouter, Query

from app.db.database import get_recent_telemetry
from app.db.models import TelemetryResponse
from datetime import datetime
import pandas as pd
from fastapi import Response
from influxdb_client import InfluxDBClient
from app.core.config import INFLUX_URL, INFLUX_TOKEN, INFLUX_ORG, INFLUX_BUCKET

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


@router.get("/export/telemetry", summary="Експорт телеметрії у CSV")
def export_telemetry():
    try:
        # Беремо дані тією ж функцією, що і для живого графіка!
        data = get_recent_telemetry()
        
        if not data:
            return Response(content="No telemetry data", status_code=404)
            
        export_data = []
        for item in data:
            row = item.dict() if hasattr(item, 'dict') else dict(item)
            
            # Перетворюємо Unix-час у нормальний формат
            ts = row.get("ts", 0)
            dt_string = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') if ts else ""
            
            solar_v = row.get("solar_v", 0)
            solar_a = row.get("solar_a", 0)
            power = round(solar_v * solar_a, 2)
            
            # Міняємо крапки на коми для коректного відображення в Excel
            export_data.append({
                "timestamp": dt_string,
                "solar_v": str(solar_v).replace('.', ','),
                "solar_a": str(solar_a).replace('.', ','),
                "actual_power_w": str(power).replace('.', ',')
            })
            
        df = pd.DataFrame(export_data)
        
        return Response(
            content=df.to_csv(index=False, sep=';'),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=telemetry_fact.csv"}
        )
    except Exception as e:
        return {"error": str(e)}

@router.get("/export/predictions", summary="Експорт прогнозів у CSV")
def export_predictions(days: int = Query(default=30, description="Дні")):
    try:
        with InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG) as client:
            query = f'''
                from(bucket: "{INFLUX_BUCKET}")
                  |> range(start: -{days}d)
                  |> filter(fn: (r) => r._measurement == "predictions")
                  |> filter(fn: (r) => r._field == "predicted_power_w")
                  |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
            '''
            tables = client.query_api().query(query, org=INFLUX_ORG)
            data = [{"timestamp": r.get_time().strftime('%Y-%m-%d %H:%M:%S'), "predicted_power_w": round(r.get_value(), 2)} for t in tables for r in t.records]
            
        df = pd.DataFrame(data)
        if df.empty:
            return Response(content="No predictions data", status_code=404)
            
        return Response(
            content=df.to_csv(index=False, sep=';'),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=predictions.csv"}
        )
    except Exception as e:
        return {"error": str(e)}