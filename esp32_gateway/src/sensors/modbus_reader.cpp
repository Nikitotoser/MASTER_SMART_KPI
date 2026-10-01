#include "modbus_reader.h"
#include "config.h"
#include <ModbusMaster.h>

// Екземпляр класу для спілкування по промисловому протоколу Modbus
ModbusMaster node;

void initModbus() {
    // Ініціалізація апаратного UART2 для шини RS-485
    Serial2.begin(9600, SERIAL_8N1, MODBUS_RX_PIN, MODBUS_TX_PIN);
    
    // Підключення до Slave-пристрою з адресою 1 (PZEM-017)
    node.begin(1, Serial2);
    
    Serial.printf("[MODBUS] Serial2 (PZEM-017) ініціалізовано на RX: %d, TX: %d\n", MODBUS_RX_PIN, MODBUS_TX_PIN);
}

// Запис показників сонячної панелі у поточний пакет телеметрії
void readSolarData(TelemetryPacket& packet) {
    // Зчитування 2 вхідних регістрів
    uint8_t result = node.readInputRegisters(0x0000, 2);
    
    if (result == node.ku8MBSuccess) {
        // PZEM-017 передає значення з множником 100, тому ділимо на 100.0f
        packet.solar.voltage = node.getResponseBuffer(0) / 100.0f;
        packet.solar.current = node.getResponseBuffer(1) / 100.0f;
        
        Serial.printf("[MODBUS] Сонячна панель: %.2f В, %.2f А\n", packet.solar.voltage, packet.solar.current);
    } else {
        // У разі помилки зв'язку — скидання значень у нуль
        Serial.printf("[MODBUS] Помилка зчитування PZEM-017. Код: 0x%02X\n", result);
        packet.solar.voltage = 0.0f;
        packet.solar.current = 0.0f;
    }
}