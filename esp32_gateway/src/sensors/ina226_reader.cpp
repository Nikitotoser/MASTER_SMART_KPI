#include "ina226_reader.h"
#include "config.h"
#include <Wire.h>
#include <INA226.h>

// Екземпляр класу для роботи з модулем INA226 (I2C адреса 0x40)
INA226 ina(0x40);

void initBatterySensor() {
    // Ініціалізація шини I2C
    Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
    
    if (!ina.begin()) {
        Serial.println("[I2C] Помилка: INA226 (батарея) не знайдено на шині.");
    } else {
        // Калібрування шунта (максимальний струм 10А, опір 0.01 Ом)
        ina.setMaxCurrentShunt(10.0, 0.01); 
        Serial.printf("[I2C] INA226 ініціалізовано (SDA: %d, SCL: %d)\n", I2C_SDA_PIN, I2C_SCL_PIN);
    }
}

// Запис показників акумулятора безпосередньо у пакет телеметрії
void readBatteryData(TelemetryPacket& packet) {
    if (ina.isConnected()) {
        packet.battery.voltage = ina.getBusVoltage();
        packet.battery.current = ina.getCurrent();
        
        Serial.printf("[I2C] Батарея: %.2f В, %.2f А\n", packet.battery.voltage, packet.battery.current);
    } else {
        // У разі апаратного збою або обриву лінії — скидання значень у нуль
        Serial.println("[I2C] Помилка зчитування даних INA226.");
        packet.battery.voltage = 0.0f;
        packet.battery.current = 0.0f;
    }
}