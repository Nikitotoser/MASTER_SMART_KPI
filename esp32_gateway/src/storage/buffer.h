#pragma once

#include <stdint.h>
#include "models.h"

// Ініціалізація або повне очищення черги буфера
void initBuffer();

// Збереження пакета телеметрії (передача за константним посиланням)
bool saveToBuffer(const TelemetryPacket& packet);

// Перевірка наявності невідправлених пакетів у масиві
bool hasBufferedData();

// Вилучення найстарішого пакета з черги з апаратним зсувом пам'яті
TelemetryPacket getFromBuffer();

// Повертає поточну кількість пакетів, що очікують на відправку
uint16_t getBufferCount();