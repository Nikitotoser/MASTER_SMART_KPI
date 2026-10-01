#pragma once

#include "models.h"

// Ініціалізація мережевих інтерфейсів (Wi-Fi, NTP, MQTT)
void initNetwork();

// Фонова підтримка та відновлення мережевих сесій
void maintainNetwork(); 

// Перевірка статусу з'єднання з маршрутизатором та MQTT-брокером
bool isNetworkConnected();

// Серіалізація та публікація телеметрії (передача за константним посиланням)
bool sendTelemetry(const TelemetryPacket& packet);