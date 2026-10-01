#pragma once

#include "models.h"

// Ініціалізація апаратних або симуляційних підсистем збору даних
void initSensors();

// Головна процедура опитування та формування консолідованого пакета телеметрії
TelemetryPacket readSensors();

// Допоміжні внутрішні процедури
TelemetryPacket readSimulatedSensors();
TelemetryPacket readRealSensors();