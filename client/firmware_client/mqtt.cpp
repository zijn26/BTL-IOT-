#include "mqtt.h"
#include <Arduino.h>
#include <WiFiClient.h>
#include <PubSubClient.h>

MQTTProtocol::MQTTProtocol() : _mqttClient(_wifiClient) {}

void MQTTProtocol::begin() {
  // Load cấu hình từ NVS
  Settings mqttSettings("mqtt", true);
  
  _broker = mqttSettings.getString("broker", "");
  _port = mqttSettings.getInt("port", 1883);
  _clientId = mqttSettings.getString("clientId", "");

  if (_broker.length() == 0) {
    Serial.println("⚠️ [MQTT] No broker configuration found in NVS!");
    Serial.println("💡 [MQTT] Please set MQTT configuration first using updateConfig()");
    return;
  }

  _mqttClient.setServer(_broker.c_str(), _port);

  Serial.printf("🔧 [MQTT] Loaded config from NVS: host=%s, port=%u\n", _broker.c_str(), _port);
  if (_user.length() > 0)
    Serial.printf("   [MQTT] user=%s\n", _user.c_str());
}

void MQTTProtocol::setCallback(MQTT_CALLBACK_SIGNATURE) {
  _mqttClient.setCallback(callback);
}

void MQTTProtocol::updateConfig(const String& broker, uint16_t port, const String& clientId) {
  // Lưu cấu hình vào NVS
  Settings mqttSettings("mqtt", true);
  _clientId = clientId;
  mqttSettings.setString("broker", broker);
  mqttSettings.setInt("port", port);
  mqttSettings.setString("clientId", clientId);
  // Cập nhật biến thành viên
  _broker = broker;
  _port = port;
  
  // Cập nhật server cho MQTT client
  _mqttClient.setServer(_broker.c_str(), _port);
  
  Serial.printf("✅ [MQTT] Configuration updated and saved to NVS:\n");
  Serial.printf("   [MQTT] Broker: %s:%u\n", _broker.c_str(), _port);
  Serial.printf("   [MQTT] Client ID: %s\n", _clientId.c_str());
}

void MQTTProtocol::loop() {
  if (!_mqttClient.connected()) {
    reconnect();
  }
  _mqttClient.loop();
}

void MQTTProtocol::reconnect() {
  if (_mqttClient.connected()) return;

  Serial.printf("🔄 Reconnecting to MQTT broker %s:%u...\n", _broker.c_str(), _port);

  while (!_mqttClient.connected()) {
    bool ok = _mqttClient.connect(_clientId.c_str());

    if (ok) {
      Serial.println("✅ MQTT connected!");
      break;
    } else {
      Serial.printf("❌ Failed, rc=%d. Retry in 5s...\n", _mqttClient.state());
      delay(5000);
    }
  }
}

void MQTTProtocol::publish(const char* topic, const String &payload, bool retained) {
  if (!_mqttClient.connected()) {
    Serial.println("⚠️ MQTT not connected, cannot publish");
    return;
  }
  _mqttClient.publish(topic, payload.c_str(), retained);
  Serial.printf("📤 Published [%s] => %s\n", topic, payload.c_str());
}

void MQTTProtocol::subscribe(const char* topic) {
  if (!_mqttClient.connected()) {
    Serial.println("⚠️ MQTT not connected, cannot subscribe");
    return;
  }
  _mqttClient.subscribe(topic);
  Serial.printf("📡 Subscribed to: %s\n", topic);
}

bool MQTTProtocol::connected() {
  return _mqttClient.connected();
}
