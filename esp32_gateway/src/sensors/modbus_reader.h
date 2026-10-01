#pragma once

#include "models.h"

// Ініціалізація апаратного інтерфейсу RS-485 та протоколу Modbus (PZEM-017)
void initModbus();

// Зчитування показників сонячної панелі та їх запис у поточний пакет телеметрії
void readSolarData(TelemetryPacket& packet);