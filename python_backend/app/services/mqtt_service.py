import logging

import paho.mqtt.client as mqtt

from app.core.config import MQTT_BROKER, MQTT_PORT, MQTT_TOPIC
from app.db.database import save_telemetry
from app.db.models import IncomingTelemetry

# Ініціалізація логера модуля
logger = logging.getLogger(__name__)


def on_connect(client: mqtt.Client, userdata, flags, rc: int):
    """Обробник успішного підключення до MQTT-брокера."""
    if rc == 0:
        logger.info("Успішне підключення до MQTT-брокера (HiveMQ).")
        client.subscribe(MQTT_TOPIC)
        logger.info("Підписано на топік телеметрії: %s", MQTT_TOPIC)
    else:
        logger.error("Помилка підключення до брокера. Код: %s", rc)


def on_disconnect(client: mqtt.Client, userdata, rc: int):
    """Обробник втрати з'єднання з брокером."""
    logger.warning("Втрачено зв'язок з MQTT-брокером. Спроба автовідновлення...")


def on_message(client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
    """Обробник та маршрутизація вхідних повідомлень телеметрії від ESP32."""
    try:
        # Pydantic V2: швидкий парсинг та валідація сирого JSON
        payload_str = msg.payload.decode()
        data = IncomingTelemetry.model_validate_json(payload_str)
        
        # Детекція апаратних збоїв на стороні мікроконтролера
        if data.solar.v == 0.0 and data.bat.v == 0.0:
            logger.warning("Апаратний збій на ESP32! Отримано нульові показники (ts=%s).", data.ts)
            
        # Розрахунок потужності для логування
        sol_p = round(data.solar.v * data.solar.i, 2)
        bat_p = round(data.bat.v * data.bat.i, 2)
        
        # Передача валідованої моделі безпосередньо в базу даних без проміжних словників
        save_telemetry(data)
        logger.info("Телеметрію збережено -> Сонце: %s Вт | Батарея: %s Вт", sol_p, bat_p)
        
    except Exception as e:
        logger.error("Отримано пошкоджений або невалідний пакет телеметрії: %s", e)


def start_mqtt():
    """Ініціалізація та запуск фонового MQTT-клієнта."""
    client = mqtt.Client()
    
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    
    logger.info("Ініціалізація з'єднання з %s:%s...", MQTT_BROKER, MQTT_PORT)
    client.connect(MQTT_BROKER, MQTT_PORT)
    client.loop_forever()