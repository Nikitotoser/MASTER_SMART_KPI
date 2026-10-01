#ifndef PIO_UNIT_TESTING

#include <Arduino.h>
#include <stdint.h>
#include "config.h"
#include "sensors.h"
#include "buffer.h"
#include "network.h"

// Таймер опитування (використання строгого типу замість unsigned long)
uint32_t lastPollTime = 0;

void setup() {
    Serial.begin(115200);
    delay(1000); 
    
    Serial.println("\n[SYS] Старт Smart Energy Gateway");

    // Ініціалізація апаратних та програмних підсистем
    initSensors();
    initBuffer();
    initNetwork();
}

void loop() {
    // Фонова підтримка з'єднання з Wi-Fi та MQTT
    maintainNetwork();

    uint32_t currentMillis = millis();
    
    // Неблокуючий таймер опитування датчиків
    if (currentMillis - lastPollTime >= SENSOR_POLL_INTERVAL_MS) {
        lastPollTime = currentMillis;

        // Зчитування актуальних показників
        TelemetryPacket newPacket = readSensors();

        // Вивантаження накопичених пакетів при наявності зв'язку
        while (isNetworkConnected() && hasBufferedData()) {
            Serial.printf("[BUF] Відправка даних з буфера. Залишок: %d\n", getBufferCount() - 1);
            
            TelemetryPacket oldPacket = getFromBuffer();
            sendTelemetry(oldPacket);
            
            delay(50); // Запобігання перевантаженню MQTT-брокера
        }

        // Маршрутизація нового пакету даних
        if (isNetworkConnected()) {
            if (!sendTelemetry(newPacket)) {
                saveToBuffer(newPacket); // Збереження при помилці транзакції
            }
        } else {
            saveToBuffer(newPacket); // Збереження при відсутності мережі
        }
    }
}

#endif