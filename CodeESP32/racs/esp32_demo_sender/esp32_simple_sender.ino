/*
 * ESP32 Simple Sensor Data Sender
 * Gửi dữ liệu nhiệt độ, độ ẩm lên MQTT Broker và CoAP Server
 * Phiên bản đơn giản - chỉ dùng HTTP POST cho CoAP
 * 
 * Yêu cầu:
 * - Thư viện: WiFi, PubSubClient, ArduinoJson, DHT sensor library
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
// WiFi settings - THAY ĐỔI THEO MẠNG CỦA BẠN
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Server settings - THAY ĐỔI IP THEO MÁY CHẠY TestMQTT.py
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
const unsigned long PACKET_INTERVAL = 200; // 200ms giữa các gói

// ==================== SETUP ====================
void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("========================================");
  Serial.println("ESP32 Sensor Data Sender");
  Serial.println("========================================");
  Serial.println("Hướng dẫn sử dụng:");
  Serial.println("1. Cấu hình WiFi và IP server trong code");
  Serial.println("2. Gõ 'test' để bắt đầu gửi 20 gói dữ liệu");
  Serial.println("3. Không gõ gì thì ESP32 sẽ không làm gì");
  Serial.println("========================================");
  
  // Khởi tạo DHT sensor
  dht.begin();
  Serial.println("DHT sensor initialized");
  
  // Kết nối WiFi
  connectToWiFi();
  
  // Kết nối MQTT
  mqttClient.setServer(mqtt_server, mqtt_port);
  mqttClient.setCallback(mqttCallback);
  connectToMQTT();
  
  Serial.println("Setup completed!");
  Serial.println("Gõ 'test' để bắt đầu...");
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
      Serial.println("========================================");
      Serial.println("Đã gửi xong 20 gói dữ liệu!");
      Serial.println("Gõ 'test' để gửi lại");
      Serial.println("========================================");
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
        Serial.println("========================================");
        Serial.println("Bắt đầu gửi 20 gói dữ liệu...");
        Serial.println("========================================");
      } else {
        Serial.println("Đang trong quá trình gửi dữ liệu, vui lòng đợi!");
      }
    } else if (input == "status") {
      printStatus();
    } else if (input == "help") {
      printHelp();
    } else {
      Serial.println("Gõ 'test' để bắt đầu gửi dữ liệu");
      Serial.println("Gõ 'status' để xem trạng thái");
      Serial.println("Gõ 'help' để xem hướng dẫn");
    }
  }
}

// ==================== KẾT NỐI WIFI ====================
void connectToWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("Đang kết nối WiFi");
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.println("WiFi đã kết nối!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println();
    Serial.println("WiFi kết nối thất bại!");
    Serial.println("Vui lòng kiểm tra SSID và password");
  }
}

// ==================== KẾT NỐI MQTT ====================
void connectToMQTT() {
  int attempts = 0;
  while (!mqttClient.connected() && attempts < 5) {
    Serial.print("Đang kết nối MQTT...");
    
    if (mqttClient.connect(mqtt_client_id)) {
      Serial.println("MQTT đã kết nối!");
      return;
    } else {
      Serial.print("MQTT kết nối thất bại, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" Thử lại sau 2 giây...");
      delay(2000);
      attempts++;
    }
  }
  
  if (!mqttClient.connected()) {
    Serial.println("MQTT kết nối thất bại sau 5 lần thử!");
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
  
  // Tạo JSON payload theo format yêu cầu
  StaticJsonDocument<300> doc;
  doc["id"] = packetCount + 1;
  doc["data"] = round(temperature * 100.0) / 100.0;  // Làm tròn 2 chữ số thập phân
  doc["time"] = millis() / 1000.0;  // Timestamp đơn giản
  doc["humidity"] = round(humidity * 100.0) / 100.0;  // Thêm độ ẩm
  doc["sensor"] = "DHT22";  // Thêm thông tin sensor
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  // Gửi qua MQTT
  bool mqttSuccess = false;
  if (mqttClient.connected()) {
    mqttSuccess = mqttClient.publish(mqtt_topic, jsonString.c_str());
  }
  
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
    if (millis() - timeout > 3000) {
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
  Serial.println("========================================");
  Serial.println("=== TRẠNG THÁI HỆ THỐNG ===");
  Serial.printf("WiFi: %s\n", WiFi.status() == WL_CONNECTED ? "Connected" : "Disconnected");
  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("IP: %s\n", WiFi.localIP().toString().c_str());
  }
  Serial.printf("MQTT: %s\n", mqttClient.connected() ? "Connected" : "Disconnected");
  Serial.printf("Test Mode: %s\n", testMode ? "ON" : "OFF");
  Serial.printf("Packets Sent: %d/%d\n", packetCount, MAX_PACKETS);
  Serial.println("========================================");
}

void printHelp() {
  Serial.println("========================================");
  Serial.println("=== HƯỚNG DẪN SỬ DỤNG ===");
  Serial.println("test    - Bắt đầu gửi 20 gói dữ liệu");
  Serial.println("status  - Xem trạng thái hệ thống");
  Serial.println("help    - Hiển thị hướng dẫn này");
  Serial.println("========================================");
}