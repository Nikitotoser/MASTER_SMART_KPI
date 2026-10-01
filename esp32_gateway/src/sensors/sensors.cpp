#include "sensors.h"
#include "config.h"
#include "modbus_reader.h"
#include "ina226_reader.h"
#include <Arduino.h>
#include <time.h>

void initSensors() {
    if (SIMULATION_MODE) {
        Serial.println("[SENSORS] Режим симуляції. Апаратні інтерфейси ігноруються.");
    } else {
        Serial.println("[SENSORS] Робочий режим. Ініціалізація апаратних модулів...");
        initModbus();
        initBatterySensor();
    }
}

// Генерація псевдовипадкових значень для тестування без фізичних датчиків
TelemetryPacket readSimulatedSensors() {
    TelemetryPacket packet;
    
    // Значення діляться на 100.0f для уникнення кастингу в double
    packet.solar.voltage = random(1700, 1900) / 100.0f;  // 17.00 - 19.00 В
    packet.solar.current = random(200, 500) / 100.0f;    // 2.00 - 5.00 А
    
    packet.battery.voltage = random(1200, 1300) / 100.0f; // 12.00 - 13.00 В
    packet.battery.current = random(-200, 200) / 100.0f;  // від -2.00 до 2.00 А
    
    return packet;
}

// Опитування фізичних шин даних
TelemetryPacket readRealSensors() {
    TelemetryPacket packet;
    
    readSolarData(packet);   // Опитування PZEM-017 (RS-485)
    readBatteryData(packet); // Опитування INA226 (I2C)
    
    return packet;
}

TelemetryPacket readSensors() {
    TelemetryPacket packet;
    
    // Маршрутизація збору даних залежно від глобальної конфігурації
    if (SIMULATION_MODE) {
        packet = readSimulatedSensors();
    } else {
        packet = readRealSensors();
    }
    
    // Фіксація глобальної мітки часу
    time_t now;
    time(&now);
    
    // Використання сучасного C++ кастингу замість (uint32_t)
    packet.timestamp = static_cast<uint32_t>(now);
    
    Serial.println("[SENSORS] Цикл збору даних успішно завершено.");
    return packet;
}