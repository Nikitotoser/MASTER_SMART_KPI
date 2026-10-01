#pragma once

#include "models.h"

// Ініціалізація I2C-шини та налаштування шунта для INA226
void initBatterySensor();

// Зчитування показників акумулятора та їх запис у поточний пакет телеметрії
void readBatteryData(TelemetryPacket& packet);