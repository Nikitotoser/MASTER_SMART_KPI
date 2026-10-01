#include <Arduino.h>
#include <unity.h>
#include <string.h> // Для функції strstr
#include "models.h"
#include "config.h"
#include "sensors.h"
#include "modbus_reader.h"
#include "ina226_reader.h"
#include <ArduinoJson.h>

void setUp(void) {}
void tearDown(void) {}

// ТЕСТ 1: Ліміт розміру MQTT-пакета (IoT Payload Constraint)
void test_mqtt_payload_size() {
    TelemetryPacket p = {1715000000, {18.45f, 4.12f}, {12.60f, -1.50f}};
    JsonDocument doc;
    doc["ts"] = p.timestamp;
    doc["sol"]["v"] = p.solar.voltage; doc["sol"]["i"] = p.solar.current;
    doc["bat"]["v"] = p.battery.voltage; doc["bat"]["i"] = p.battery.current;
    
    char output[256];
    size_t payload_len = serializeJson(doc, output);
    
    // Пакет для IoT має бути максимально компактним (< 128 байт)
    TEST_ASSERT_LESS_THAN_MESSAGE(128, payload_len, "JSON payload exceeds optimal IoT size limits!");
}

// ТЕСТ 2: Апаратна відмовостійкість (Hardware Fault Tolerance)
void test_hardware_fault_tolerance() {
    TelemetryPacket p;
    // Штучно забруднюємо структуру некоректними даними
    p.solar.voltage = 999.9f; 
    p.solar.current = -500.0f;

    // Спроба читання з відключеного/зламаного датчика
    readSolarData(p); 
    
    // Драйвер зобов'язаний перехопити помилку та обнулити показники
    TEST_ASSERT_EQUAL_FLOAT_MESSAGE(0.0f, p.solar.voltage, "Faulty sensor did not return 0.0 Volts!");
    TEST_ASSERT_EQUAL_FLOAT_MESSAGE(0.0f, p.solar.current, "Faulty sensor did not return 0.0 Amps!");
}

// ТЕСТ 3: Монотонність часових міток (Monotonic Timestamp)
void test_monotonic_timestamp() {
    TelemetryPacket p1 = readSensors();
    delay(50);
    TelemetryPacket p2 = readSensors();
    
    // Перевірка консистентності часового ряду (час не може йти назад)
    TEST_ASSERT_GREATER_OR_EQUAL_UINT32_MESSAGE(p1.timestamp, p2.timestamp, "Timestamp moved backwards!");
}

// ТЕСТ 4: Цілісність серіалізації від'ємних значень (Discharge Integrity)
void test_negative_current_serialization() {
    JsonDocument doc;
    // Імітація режиму жорсткого розряду акумулятора
    float discharge_current = -5.25f; 
    doc["bat_i"] = discharge_current;
    
    char output[128];
    serializeJson(doc, output);
    
    // Перевірка наявності знака мінус після серіалізації
    TEST_ASSERT_NOT_NULL_MESSAGE(strstr(output, "-5.25"), "Negative discharge current was lost during serialization!");
}

// ТЕСТ 5: Навантажувальне тестування симулятора (Boundary Stress Test)
void test_simulator_boundary_conditions() {
    // 100 ітерацій для виявлення аномальних відхилень
    for(uint8_t i = 0; i < 100; i++) {
        TelemetryPacket p = readSimulatedSensors();
        
        // Фізичні межі: напруга панелі [0.0; 25.0]
        TEST_ASSERT_TRUE_MESSAGE(p.solar.voltage >= 0.0f && p.solar.voltage <= 25.0f, "Solar voltage Out of Bounds!");
        // Фізичні межі: струм акумулятора [-10.0; 10.0]
        TEST_ASSERT_TRUE_MESSAGE(p.battery.current >= -10.0f && p.battery.current <= 10.0f, "Battery current Out of Bounds!");
    }
}

// ГОЛОВНА ТОЧКА ВХОДУ ДЛЯ ТЕСТІВ (PlatformIO Unity)
void setup() {
    Serial.begin(115200);

    initModbus();
    initBatterySensor();

    delay(2000);
    UNITY_BEGIN(); 
    
    RUN_TEST(test_mqtt_payload_size);
    RUN_TEST(test_hardware_fault_tolerance);
    RUN_TEST(test_monotonic_timestamp);
    RUN_TEST(test_negative_current_serialization);
    RUN_TEST(test_simulator_boundary_conditions);
    
    UNITY_END(); 
}

void loop() {
    delay(1000);
}