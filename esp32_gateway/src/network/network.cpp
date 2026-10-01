#include "network.h"
#include "config.h"
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <time.h>

WiFiClient espClient;
PubSubClient mqttClient(espClient);

void initNetwork() {
    WiFi.mode(WIFI_STA); 
    mqttClient.setServer(MQTT_BROKER_IP, MQTT_BROKER_PORT);

    // Синхронізація часу через NTP
    configTime(0, 0, "pool.ntp.org", "time.nist.gov");
    setenv("TZ", "EET-2EEST,M3.5.0/3,M10.5.0/4", 1); 
    tzset();

    Serial.println("[NET] Мережеві підсистеми ініціалізовано.");
}

bool isNetworkConnected() {
    return WiFi.status() == WL_CONNECTED && mqttClient.connected();
}

void maintainNetwork() {
    // Відновлення Wi-Fi з'єднання (обмежено 10 спробами для уникнення блокування)
    if (WiFi.status() != WL_CONNECTED) {
        Serial.print("[NET] Відновлення Wi-Fi");
        WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
        
        uint8_t attempts = 0; // Економія пам'яті
        while (WiFi.status() != WL_CONNECTED && attempts < 10) {
            delay(500);
            Serial.print(".");
            attempts++;
        }
        Serial.println();
    }

    // Відновлення сесії MQTT
    if (WiFi.status() == WL_CONNECTED && !mqttClient.connected()) {
        Serial.print("[NET] Підключення до MQTT...");
        if (mqttClient.connect(MQTT_CLIENT_ID)) {
            Serial.println(" ОК");
        } else {
            Serial.printf(" Помилка, код: %d\n", mqttClient.state());
        }
    }

    // Обробка вхідних повідомлень та keep-alive MQTT
    if (mqttClient.connected()) {
        mqttClient.loop();
    }
}

// Передача пакета за константним посиланням (const &) для оптимізації пам'яті
bool sendTelemetry(const TelemetryPacket& packet) {
    if (!isNetworkConnected()) {
        return false;
    }

    JsonDocument doc;

    doc["ts"] = packet.timestamp;
    
    // Дані сонячної панелі
    doc["solar"]["v"] = packet.solar.voltage;
    doc["solar"]["i"] = packet.solar.current;
    
    // Дані акумулятора
    doc["bat"]["v"] = packet.battery.voltage;
    doc["bat"]["i"] = packet.battery.current;

    char jsonBuffer[256];
    serializeJson(doc, jsonBuffer);

    Serial.printf("[NET] Відправка: %s\n", jsonBuffer);
    
    return mqttClient.publish(MQTT_TOPIC_TELEMETRY, jsonBuffer);
}