import logging

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from app.core.config import INFLUX_URL, INFLUX_TOKEN, INFLUX_ORG, INFLUX_BUCKET
from app.db.models import IncomingTelemetry, TelemetryResponse

# Ініціалізація логера модуля
logger = logging.getLogger(__name__)

# Ініціалізація клієнта бази даних InfluxDB
client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)
query_api = client.query_api()


def save_telemetry(data: IncomingTelemetry) -> bool:
    """Зберігає валідований пакет телеметрії в InfluxDB."""
    try:
        # Формування точки даних з типізованої моделі Pydantic
        point = (
            Point("energy_metrics")
            .tag("device", "esp32_gateway")
            .time(data.ts, write_precision='s')
            .field("solar_v", float(data.solar.v))
            .field("solar_a", float(data.solar.i))
            .field("bat_v", float(data.bat.v))
            .field("bat_a", float(data.bat.i))
        )
        
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
        return True
    except Exception as e:
        logger.error("Помилка транзакції запису в InfluxDB: %s", e)
        return False


def get_recent_telemetry() -> list[TelemetryResponse]:
    """Отримує останні 500 записів за 24 години для рендерингу на фронтенді."""
    query = f'''
        from(bucket: "{INFLUX_BUCKET}")
        |> range(start: -24h)
        |> filter(fn: (r) => r._measurement == "energy_metrics")
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> sort(columns: ["_time"], desc: true)
        |> limit(n: 500)
    '''
    try:
        result = query_api.query(org=INFLUX_ORG, query=query)
        records: list[TelemetryResponse] = []
        
        # Парсинг відповіді БД у строгі Pydantic моделі
        for table in result:
            for record in table.records:
                records.append(
                    TelemetryResponse(
                        ts=int(record.get_time().timestamp()),
                        solar_v=record.values.get("solar_v", 0.0),
                        solar_a=record.values.get("solar_a", 0.0),
                        bat_v=record.values.get("bat_v", 0.0),
                        bat_a=record.values.get("bat_a", 0.0)
                    )
                )
        return records
    except Exception as e:
        logger.error("Помилка запиту на читання з InfluxDB: %s", e)
        return []