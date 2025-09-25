#include <WiFi.h>
#include <PubSubClient.h>
#include "DHT.h"

// ==== WiFi Info ====
const char* ssid = "TaoManhDuc";
const char* password = "02092606";

// ==== HiveMQ Broker Info ====
const char* mqtt_server = "mqtt-dashboard.com";  // Public broker miễn phí
const int mqtt_port = 8884;
const char* pubTopic = "doamnhietdo";        // Topic publish dữ liệu DHT11
const char* subTopic = "ledstate";        // Topic subscribe để điều khiển LED
const char* mqtt_username = "hung";
const char* mqtt_password = "123";  // điền password của bạn
const char* clientID = "hungvungoc3";
WiFiClient espClient;
PubSubClient client(espClient);

// ==== LED Pin ====
#define LED_PIN 2   // LED trên board ESP32 thường nằm ở GPIO2

// ==== DHT11 Config ====
#define DHTPIN 4       // GPIO4
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

// Hàm callback khi có message từ broker
void callback(char* topic, byte* message, unsigned int length) {
  Serial.print("📩 Nhận message từ topic: ");
  Serial.println(topic);

  String msg;
  for (unsigned int i = 0; i < length; i++) {
    msg += (char)message[i];
  }
  Serial.println("👉 Nội dung: " + msg);

  // Kiểm tra message để bật/tắt LED
  if (msg == "ON") {
    digitalWrite(LED_PIN, HIGH);
    Serial.println("💡 LED bật");
  } else if (msg == "OFF") {
    digitalWrite(LED_PIN, LOW);
    Serial.println("💡 LED tắt");
  }
}

// Kết nối lại MQTT khi bị mất
void reconnect() {
  while (!client.connected()) {
    Serial.print("🔄 Đang kết nối MQTT...");
    if (client.connect("ESP32Client")) { // Client ID, có thể đặt tùy ý
      Serial.println("✅ Đã kết nối MQTT!");
      client.subscribe(subTopic); // Đăng ký topic để nhận điều khiển
    } else {
      Serial.print("❌ Lỗi, rc=");
      Serial.print(client.state());
      Serial.println(" -> thử lại sau 5s");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  dht.begin();

  // Kết nối WiFi
  Serial.print("🔌 Đang kết nối WiFi");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ WiFi kết nối thành công!");
  Serial.print("📡 Địa chỉ IP ESP32: ");
  Serial.println(WiFi.localIP());

  // Cấu hình MQTT
  client.setServer(mqtt_server, mqtt_port);
  client.setClientId(clientID);
  client.setCredentials(mqtt_username, mqtt_password);
  client.setKeepAlive(60);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // Publish dữ liệu DHT11 mỗi 10 giây
  static unsigned long lastMsg = 0;
  if (millis() - lastMsg > 10000) {
    lastMsg = millis();

    float h = dht.readHumidity();
    float t = dht.readTemperature();

    if (isnan(h) || isnan(t)) {
      Serial.println("⚠️ Lỗi đọc cảm biến DHT!");
      return;
    }

    // Ghép dữ liệu thành JSON chuỗi
    String payload = "{\"temperature\":" + String(t) + ",\"humidity\":" + String(h) + "}";
    client.publish(pubTopic, payload.c_str());
    Serial.println("📤 Publish DHT11: " + payload);
  }
}
