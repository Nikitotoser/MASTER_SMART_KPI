from pydantic import BaseModel, Field, ConfigDict

class SensorData(BaseModel):
    """Валідаційна схема для показників одного джерела живлення."""
    v: float = Field(..., description="Напруга (Вольти)")
    i: float = Field(..., description="Струм (Ампери)")

class IncomingTelemetry(BaseModel):
    """Схема вхідного JSON-пакета телеметрії від ESP32 через MQTT."""
    ts: int = Field(..., description="Мітка часу (UNIX timestamp)")
    solar: SensorData = Field(..., description="Дані сонячної панелі")
    bat: SensorData = Field(..., description="Дані акумуляторної батареї")

class TelemetryResponse(BaseModel):
    """Пласка схема вихідних даних для оптимізації рендерингу графіків на фронтенді."""
    ts: int = Field(..., description="Мітка часу (UNIX timestamp)")
    solar_v: float = Field(..., description="Напруга сонячної панелі (В)")
    solar_a: float = Field(..., description="Струм сонячної панелі (А)")
    bat_v: float = Field(..., description="Напруга акумулятора (В)")
    bat_a: float = Field(..., description="Струм акумулятора (А)")

    model_config = ConfigDict(from_attributes=True)