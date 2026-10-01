import logging
import paho.mqtt.client as mqtt
from pydantic import ValidationError

from app.core.config import MQTT_BROKER, MQTT_PORT, MQTT_TOPIC
from app.models import IncomingTelemetry
from app.db.database import save_telemetry

logger = logging.getLogger(__name__)


def on_connect(client: mqtt.Client, userdata, flags, rc: int) -> None:
    """Обробник успішного підключення до MQTT-брокера."""
    if rc == 0:
        logger.info("Підключено до MQTT брокера. Слухаємо топік: %s", MQTT_TOPIC)
        client.subscribe(MQTT_TOPIC)
    else:
        logger.error("Помилка підключення до брокера. Код: %s", rc)


def on_disconnect(client: mqtt.Client, userdata, rc: int) -> None:
    """Обробник втрати зв'язку з брокером."""
    if rc != 0:
        logger.warning("Неочікувано втрачено зв'язок з MQTT брокером. Спроба автоматичного перепідключення...")
    else:
        logger.info("Відключено від MQTT брокера.")


def on_message(client: mqtt.Client, userdata, msg: mqtt.MQTTMessage) -> None:
    """Обробник вхідних повідомлень телеметрії."""
    try:
        # Розпаковуємо та жорстко валідуємо JSON через Pydantic-модель
        payload_str = msg.payload.decode('utf-8')
        data = IncomingTelemetry.model_validate_json(payload_str)
        
        # Вираховуємо потужність суто для логування
        solar_p = round(data.solar.voltage * data.solar.current, 2)
        bat_p = round(data.battery.voltage * data.battery.current, 2)
        
        logger.info("MQTT: Сонце %s Вт | Батарея %s Вт", solar_p, bat_p)

        # Передаємо весь валідований об'єкт безпосередньо в базу даних
        save_telemetry(data)
        
    except ValidationError as e:
        logger.error("Помилка валідації JSON з MQTT (пошкоджені дані): %s", e)
    except Exception as e:
        logger.error("Неочікувана помилка обробки MQTT повідомлення: %s", e, exc_info=True)


def start_mqtt() -> None:
    """Запуск фонового MQTT-клієнта для ML-мікросервісу."""
    try:
        # Використовуємо унікальний Client ID, щоб не конфліктувати з основним бекендом
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "Edge_ML_Service")
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        client.on_message = on_message
        
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        logger.info("MQTT клієнт (Edge ML) запущено у фоновому режимі.")
    except Exception as e:
        logger.critical("КРИТИЧНА ПОМИЛКА запуску MQTT клієнта: %s", e, exc_info=True)