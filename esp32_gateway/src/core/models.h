#pragma once

#include <stdint.h>

// Показники з одного джерела живлення
struct SensorData {
    float voltage = 0.0f; // Напруга (В)
    float current = 0.0f; // Струм (А)
};

// Консолідований пакет телеметрії за один цикл опитування
struct TelemetryPacket {
    uint32_t timestamp = 0; // Час генерації пакету (мс)
    SensorData solar;       // Дані сонячної панелі
    SensorData battery;     // Дані акумуляторної батареї
};