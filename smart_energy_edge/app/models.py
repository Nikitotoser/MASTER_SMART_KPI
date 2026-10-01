from pydantic import BaseModel, Field, ConfigDict

class SensorData(BaseModel):
    """Схема даних для одного датчика з мапінгом компактних JSON-ключів."""
    voltage: float = Field(..., alias="v", description="Напруга (В)")
    current: float = Field(..., alias="i", description="Струм (А)")

    # Дозволяє звертатися до полів як за аліасами, так і за реальними іменами
    model_config = ConfigDict(populate_by_name=True)

class IncomingTelemetry(BaseModel):
    """Схема вхідного пакета телеметрії для ML-мікросервісу."""
    timestamp: int = Field(..., alias="ts", description="Час збору даних (UNIX timestamp)")
    solar: SensorData = Field(..., description="Показники сонячної панелі")
    battery: SensorData = Field(..., alias="bat", description="Показники акумуляторної батареї")

    model_config = ConfigDict(populate_by_name=True)