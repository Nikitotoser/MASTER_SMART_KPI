#include "buffer.h"
#include "config.h"
#include <Arduino.h>
#include <string.h>

// Масив в оперативній пам'яті для тимчасового зберігання пакетів
TelemetryPacket ramBuffer[BUFFER_MAX_SIZE];
uint16_t bufferCount = 0;

void initBuffer() {
    bufferCount = 0;
    Serial.println("[BUF] RAM буфер ініціалізовано.");
}

// Передача пакета за константним посиланням для мінімізації витрат пам'яті
bool saveToBuffer(const TelemetryPacket& packet) {
    if (bufferCount < BUFFER_MAX_SIZE) {
        ramBuffer[bufferCount] = packet;
        bufferCount++;
        
        Serial.printf("[BUF] Дані збережено локально. Заповненість: %d/%d\n", bufferCount, BUFFER_MAX_SIZE);
        return true;
    } else {
        // Захист від виходу за межі масиву
        Serial.println("[BUF] ПОМИЛКА: Переповнення буфера! Пакет відкинуто.");
        return false;
    }
}

bool hasBufferedData() {
    return bufferCount > 0;
}

TelemetryPacket getFromBuffer() {
    // Зберігаємо найстаріший пакет (перший у черзі)
    TelemetryPacket p = ramBuffer[0];
    
    // Апаратний зсув блоку пам'яті вліво замість повільного циклу for
    if (bufferCount > 1) {
        memmove(&ramBuffer[0], &ramBuffer[1], sizeof(TelemetryPacket) * (bufferCount - 1));
    }
    
    bufferCount--;
    return p;
}

// Повертає поточну кількість пакетів у черзі
uint16_t getBufferCount() {
    return bufferCount;
}