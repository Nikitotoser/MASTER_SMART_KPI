#pragma once

// Режим роботи: true - генерація тестових даних, false - опитування реальних датчиків
constexpr bool SIMULATION_MODE = true;

// Мережеві налаштування Wi-Fi
constexpr char WIFI_SSID[] = "Vega";
constexpr char WIFI_PASSWORD[] = "12345678";

// Налаштування MQTT-брокера
constexpr char MQTT_BROKER_IP[] = "broker.hivemq.com";
constexpr int MQTT_BROKER_PORT = 1883;
constexpr char MQTT_CLIENT_ID[] = "ESP32_SmartEnergy_Gateway";
constexpr char MQTT_TOPIC_TELEMETRY[] = "smart_energy/telemetry";

// Таймінги та буферизація
constexpr int SENSOR_POLL_INTERVAL_MS = 10000; // Інтервал опитування датчиків (мс)
constexpr int BUFFER_MAX_SIZE = 50;            // Максимальний розмір буфера при втраті з'єднання

// Апаратні піни мікроконтролера: Шина RS-485 (Сонячна панель / Modbus)
constexpr int MODBUS_RX_PIN = 16;
constexpr int MODBUS_TX_PIN = 17;

// Апаратні піни мікроконтролера: Шина I2C (Батарея / INA226)
constexpr int I2C_SDA_PIN = 21;
constexpr int I2C_SCL_PIN = 22;