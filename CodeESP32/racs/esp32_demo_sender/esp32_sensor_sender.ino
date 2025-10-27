/*
 * ESP32 Sensor Data Sender
 * Gửi dữ liệu nhiệt độ, độ ẩm lên MQTT Broker và CoAP Server
 * 
 * Yêu cầu:
 * - Thư viện: WiFi, PubSubClient, ArduinoJson, CoAPSimple
 * - Cảm biến: DHT22 hoặc DHT11
 * - Kết nối: WiFi
 * 
 * Cách sử dụng:
 * - Gõ "test" vào Serial Monitor để bắt đầu gửi 20 gói dữ liệu
 * - Không gõ gì thì ESP32 sẽ không làm gì
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <DHT.h>

// ==================== CẤU HÌNH ====================
// WiFi settings
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Server settings
const char* mqtt_server = "192.168.1.100";  // IP của máy chạy TestMQTT.py
const int mqtt_port = 1883;
const char* coap_server = "192.168.1.100";  // IP của máy chạy TestMQTT.py
const int coap_port = 5683;

// MQTT settings
const char* mqtt_topic = "test/demo";
const char* mqtt_client_id = "esp32_sensor";

// CoAP settings
const char* coap_path = "/test/demo";

// Sensor settings
#define DHT_PIN 4
#define DHT_TYPE DHT22

// ==================== BIẾN TOÀN CỤC ====================
WiFiClient espClient;
PubSubClient mqttClient(espClient);
DHT dht(DHT_PIN, DHT_TYPE);

bool testMode = false;
int packetCount = 0;
const int MAX_PACKETS = 20;
unsigned long lastPacketTime = 0;
const unsigned long PACKET_INTERVAL = 100; // 100ms giữa các gói

// ==================== SETUP ====================
void setup() {
  Serial.begin(115200);
  Serial.println("ESP32 Sensor Data Sender");
  Serial.println("Gõ 'test' để bắt đầu gửi 20 gói dữ liệu");
  
  // Khởi tạo DHT sensor
  dht.begin();
  
  // Kết nối WiFi
  connectToWiFi();
  
  // Kết nối MQTT
  mqttClient.setServer(mqtt_server, mqtt_port);
  mqttClient.setCallback(mqttCallback);
  connectToMQTT();
}

// ==================== LOOP CHÍNH ====================
void loop() {
  // Kiểm tra Serial input
  checkSerialInput();
  
  // Duy trì kết nối MQTT
  if (!mqttClient.connected()) {
    connectToMQTT();
  }
  mqttClient.loop();
  
  // Nếu đang trong chế độ test
  if (testMode) {
    if (packetCount < MAX_PACKETS) {
      if (millis() - lastPacketTime >= PACKET_INTERVAL) {
        sendSensorData();
        lastPacketTime = millis();
        packetCount++;
      }
    } else {
      // Hoàn thành gửi 20 gói
      testMode = false;
      packetCount = 0;
      Serial.println("Đã gửi xong 20 gói dữ liệu!");
      Serial.println("Gõ 'test' để gửi lại");
    }
  }
  
  delay(10);
}

// ==================== KIỂM TRA SERIAL INPUT ====================
void checkSerialInput() {
  if (Serial.available()) {
    String input = Serial.readString();
    input.trim();
    
    if (input == "test") {
      if (!testMode) {
        testMode = true;
        packetCount = 0;
        lastPacketTime = 0;
        Serial.println("Bắt đầu gửi 20 gói dữ liệu...");
      } else {
        Serial.println("Đang trong quá trình gửi dữ liệu, vui lòng đợi!");
      }
    } else {
      Serial.println("Gõ 'test' để bắt đầu gửi dữ liệu");
    }
  }
}

// ==================== KẾT NỐI WIFI ====================
void connectToWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("Đang kết nối WiFi");
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println();
  Serial.println("WiFi đã kết nối!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

// ==================== KẾT NỐI MQTT ====================
void connectToMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("Đang kết nối MQTT...");
    
    if (mqttClient.connect(mqtt_client_id)) {
      Serial.println("MQTT đã kết nối!");
    } else {
      Serial.print("MQTT kết nối thất bại, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" Thử lại sau 5 giây...");
      delay(5000);
    }
  }
}

// ==================== CALLBACK MQTT ====================
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  // Không cần xử lý callback cho bài này
}

// ==================== GỬI DỮ LIỆU SENSOR ====================
void sendSensorData() {
  // Đọc dữ liệu từ DHT sensor
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  
  // Kiểm tra dữ liệu hợp lệ
  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("Lỗi đọc dữ liệu từ DHT sensor!");
    return;
  }
  
  // Tạo JSON payload
  StaticJsonDocument<200> doc;
  doc["id"] = packetCount + 1;
  doc["data"] = temperature;  // Sử dụng nhiệt độ làm data chính
  doc["time"] = millis() / 1000.0;  // Timestamp đơn giản
  doc["humidity"] = humidity;  // Thêm độ ẩm
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  // Gửi qua MQTT
  bool mqttSuccess = mqttClient.publish(mqtt_topic, jsonString.c_str());
  
  // Gửi qua CoAP (HTTP POST)
  bool coapSuccess = sendCoAPData(jsonString);
  
  // In kết quả
  Serial.printf("[%d/%d] Temp: %.2f°C, Humidity: %.2f%% | MQTT: %s | CoAP: %s\n", 
                packetCount + 1, MAX_PACKETS, temperature, humidity,
                mqttSuccess ? "OK" : "FAIL", coapSuccess ? "OK" : "FAIL");
}

// ==================== GỬI DỮ LIỆU COAP ====================
bool sendCoAPData(String jsonData) {
  WiFiClient client;
  
  if (!client.connect(coap_server, coap_port)) {
    return false;
  }
  
  // Tạo HTTP POST request (CoAP server có thể nhận HTTP)
  String request = "POST " + String(coap_path) + " HTTP/1.1\r\n";
  request += "Host: " + String(coap_server) + ":" + String(coap_port) + "\r\n";
  request += "Content-Type: application/json\r\n";
  request += "Content-Length: " + String(jsonData.length()) + "\r\n";
  request += "Connection: close\r\n\r\n";
  request += jsonData;
  
  client.print(request);
  
  // Đọc response (đơn giản)
  unsigned long timeout = millis();
  while (client.available() == 0) {
    if (millis() - timeout > 5000) {
      client.stop();
      return false;
    }
  }
  
  // Đọc và bỏ qua response
  while (client.available()) {
    client.read();
  }
  
  client.stop();
  return true;
}

// ==================== HÀM TIỆN ÍCH ====================
void printStatus() {
  Serial.println("=== TRẠNG THÁI HỆ THỐNG ===");
  Serial.printf("WiFi: %s\n", WiFi.status() == WL_CONNECTED ? "Connected" : "Disconnected");
  Serial.printf("MQTT: %s\n", mqttClient.connected() ? "Connected" : "Disconnected");
  Serial.printf("Test Mode: %s\n", testMode ? "ON" : "OFF");
  Serial.printf("Packets Sent: %d/%d\n", packetCount, MAX_PACKETS);
  Serial.println("==========================");
}