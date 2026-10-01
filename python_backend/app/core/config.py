import os
from typing import Final

"""
Конфігураційний модуль бекенду.
Зчитує параметри середовища з резервними значеннями за замовчуванням.
Використовує строгу типізацію для захисту констант від випадкового перезапису.
"""

# Налаштування підключення до MQTT-брокера
MQTT_BROKER: Final[str] = os.getenv("MQTT_BROKER", "broker.hivemq.com")
MQTT_PORT: Final[int] = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC: Final[str] = os.getenv("MQTT_TOPIC", "smart_energy/telemetry")

# Налаштування підключення до бази даних часових рядів (InfluxDB)
INFLUX_URL: Final[str] = os.getenv("INFLUX_URL", "http://localhost:8086")
INFLUX_TOKEN: Final[str] = os.getenv("INFLUX_TOKEN", "smart-energy-super-secret-token")
INFLUX_ORG: Final[str] = os.getenv("INFLUX_ORG", "KPI")
INFLUX_BUCKET: Final[str] = os.getenv("INFLUX_BUCKET", "smart_energy")

# Налаштування мережевих інтерфейсів FastAPI
API_HOST: Final[str] = os.getenv("API_HOST", "0.0.0.0")
API_PORT: Final[int] = int(os.getenv("API_PORT", "8000"))