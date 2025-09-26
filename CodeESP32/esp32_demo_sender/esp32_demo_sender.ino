/*
 * ESP32 Demo Data Sender
 * Gửi dữ liệu giả lập lên MQTT Broker và CoAP Server
 * Không cần cảm biến thật - dùng dữ liệu giả lập
 * 
 * Yêu cầu:
 * - Thư viện: WiFi, PubSubClient, ArduinoJson
 * - Kết nối: WiFi
 * 
 * Cách sử dụng:
 * - Gõ "test" vào Serial Monitor để bắt đầu gửi 20 gói dữ liệu
 * - Không gõ gì thì ESP32 sẽ không làm gì
 */

#include <WiFi.h>
#include <PubSubClient.h> // mqtt server
#include <ArduinoJson.h>
#include <WiFiUDP.h>
#include "time.h"

#define DHTPIN 19
// ==================== CẤU HÌNH ====================
// WiFi settings - THAY ĐỔI THEO MẠNG CỦA BẠN
const char* ssid = "310";
const char* password = "88969696";

// Server settings - THAY ĐỔI IP THEO MÁY CHẠY TestMQTT.py
const char* mqtt_server = "192.168.3.4";  // IP của máy chạy TestMQTT.py
const int mqtt_port = 20904;
const char* coap_server = "192.168.3.4";  // IP của máy chạy TestMQTT.py  
const int coap_port = 2606;

// NTP settings
const char* ntpServer = "pool.ntp.org";

// MQTT settings
const char* mqtt_topic = "test/demo";
const char* mqtt_client_id = "esp32_demo";

// CoAP settings
const char* coap_path = "/test/demo";

// ==================== BIẾN TOÀN CỤC ====================
WiFiClient espClient;
WiFiUDP udp;
PubSubClient mqttClient(espClient);

bool testMode = false;
int packetCount = 0;
const int MAX_PACKETS = 20;
unsigned long lastPacketTime = 0;
const unsigned long PACKET_INTERVAL = 200; // 200ms giữa các gói

// Dữ liệu giả lập
float baseTemp = 25.0;
float baseHumidity = 60.0;

// ==================== SETUP ====================
void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("========================================");
  Serial.println("ESP32 Demo Data Sender");
  Serial.println("========================================");
  Serial.println("Hướng dẫn sử dụng:");
  Serial.println("1. Cấu hình WiFi và IP server trong code");
  Serial.println("2. Gõ 'test' để bắt đầu gửi 20 gói dữ liệu");
  Serial.println("3. Không gõ gì thì ESP32 sẽ không làm gì");
  Serial.println("4. Dữ liệu sẽ được giả lập (không cần cảm biến)");
  Serial.println("========================================");
  
  // Kết nối WiFi
  connectToWiFi();
  
  // Kết nối MQTT
  mqttClient.setServer(mqtt_server, mqtt_port);
  mqttClient.setCallback(mqttCallback);
  connectToMQTT();
  
  // Cấu hình NTP time
  configTime(0, 0, ntpServer); // không cộng offset

  
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
        sendDemoData();
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
        Serial.println("Bắt đầu gửi 20 gói dữ liệu giả lập...");
        Serial.println("========================================");
      } else {
        Serial.println("Đang trong quá trình gửi dữ liệu, vui lòng đợi!");
      }
    } else if (input == "status") {
      printStatus();
    } else if (input == "help") {
      printHelp();
    } else if (input == "reset") {
      resetData();
    } else {
      Serial.println("Gõ 'test' để bắt đầu gửi dữ liệu");
      Serial.println("Gõ 'status' để xem trạng thái");
      Serial.println("Gõ 'help' để xem hướng dẫn");
      Serial.println("Gõ 'reset' để reset dữ liệu");
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
  
}

// ==================== GỬI DỮ LIỆU GIẢ LẬP ====================
void sendDemoData() {
  // Tạo dữ liệu giả lập với một chút biến thiên
  float temperature = baseTemp + random(-50, 50) / 10.0;  // ±5°C
  float humidity = baseHumidity + random(-200, 200) / 10.0;  // ±20%
  
  // Giới hạn giá trị hợp lý
  temperature = constrain(temperature, 15.0, 35.0);
  humidity = constrain(humidity, 30.0, 90.0);
  
  // Get precise timestamp with microsecond accuracy using gettimeofday
  struct timeval tv;
  gettimeofday(&tv, NULL);
  
  // tv.tv_sec  = số giây từ 1970
  // tv.tv_usec = micro-giây
  unsigned long long timestamp_ms = (unsigned long long)tv.tv_sec * 1000ULL + (tv.tv_usec / 1000ULL);
  unsigned long long timestamp_us = (unsigned long long)tv.tv_sec * 1000000ULL + tv.tv_usec;
  
  // Format time as HH:MM:SS
  struct tm timeinfo;
  localtime_r(&tv.tv_sec, &timeinfo);
  char timeStr[20];
  strftime(timeStr, sizeof(timeStr), "%H:%M:%S", &timeinfo);
  
  // Tạo JSON payload theo format yêu cầu
  StaticJsonDocument<300> doc;
  doc["id"] = packetCount + 1;
  doc["data"] = round(temperature * 100.0) / 100.0;                   // timestamp dạng epoch (số giây từ 1970)
  doc["timestamp_ms"] = timestamp_ms;           // timestamp với độ chính xác mili giây
  doc["timestamp_us"] = timestamp_us;           // timestamp với độ chính xác micro giây
  doc["humidity"] = round(humidity * 100.0) / 100.0;
  doc["sensor"] = "DEMO";
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  // Gửi qua MQTT
  bool mqttSuccess = false;
  if (mqttClient.connected()) {
    mqttSuccess = mqttClient.publish(mqtt_topic, jsonString.c_str());
  }
  
  // Gửi qua CoAP (HTTP POST)
  bool coapSuccess = sendCoAPData("/test/demo" , jsonString);
  
  // In kết quả với timestamp chính xác
  Serial.println("[%d/%d] Temp: %.2f°C, Humidity: %.2f%%/n", 
                packetCount + 1, MAX_PACKETS, temperature, humidity
               );
}

// ==================== GỬI DỮ LIỆU COAP ====================
int addOption(uint8_t *packet, int index, uint16_t optNum, uint16_t &lastOption,
              const uint8_t *value, uint8_t length) {
  uint16_t delta = optNum - lastOption;
  packet[index++] = (delta << 4) | (length & 0x0F);
  memcpy(&packet[index], value, length);
  index += length;
  lastOption = optNum;
  return index;
}

int setUriPath(uint8_t *packet, int index, String path, uint16_t &lastOption) {
  // Bỏ dấu "/" đầu nếu có
  if (path.startsWith("/")) {
    path = path.substring(1);
  }

  int from = 0;
  while (from < path.length()) {
    int slash = path.indexOf('/', from);
    String segment;
    if (slash == -1) {
      segment = path.substring(from);
      from = path.length();
    } else {
      segment = path.substring(from, slash);
      from = slash + 1;
    }

    if (segment.length() > 0) {
      index = addOption(packet, index, 11, lastOption,
                        (const uint8_t*)segment.c_str(),
                        segment.length());
    }
  }
  return index;
}

// ====== HÀM GỬI COAP POST ======
bool sendCoAPData(String path, String jsonData) {
  uint8_t packet[256];
  int index = 0;

  // ==== CoAP Header ====
  uint8_t ver = 1;       // Version = 1
  uint8_t t   = 0;       // Confirmable
  uint8_t tkl = 1;       // Token length
  uint8_t code = 0x02;   // POST
  uint16_t msgID = random(0, 65535);
  uint8_t token = 0xA1;

  // Byte 0
  packet[index++] = (ver << 6) | (t << 4) | (tkl & 0x0F);
  // Byte 1
  packet[index++] = code;
  // Message ID
  packet[index++] = (msgID >> 8) & 0xFF;
  packet[index++] = msgID & 0xFF;
  // Token
  packet[index++] = token;

  // ==== Options ====
  uint16_t lastOption = 0;

  // Uri-Path
  index = setUriPath(packet, index, path, lastOption);

  // Content-Format = application/json (50)
  uint8_t fmt = 50;
  index = addOption(packet, index, 12, lastOption, &fmt, 1);

  // ==== Payload ====
  packet[index++] = 0xFF; // payload marker
  memcpy(&packet[index], jsonData.c_str(), jsonData.length());
  index += jsonData.length();

  // ==== Send ====
  udp.beginPacket(coap_server, coap_port);
  udp.write(packet, index);
  udp.endPacket();

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
  Serial.printf("Base Temp: %.1f°C\n", baseTemp);
  Serial.printf("Base Humidity: %.1f%%\n", baseHumidity);
  
  // Show current time
  struct timeval tv;
  gettimeofday(&tv, NULL);
  struct tm timeinfo;
  localtime_r(&tv.tv_sec, &timeinfo);
  char timeStr[30];
  strftime(timeStr, sizeof(timeStr), "%Y-%m-%d %H:%M:%S", &timeinfo);
  Serial.printf("Current Time: %s.%06lu\n", timeStr, tv.tv_usec);
  Serial.println("========================================");
}

void printHelp() {
  Serial.println("========================================");
  Serial.println("=== HƯỚNG DẪN SỬ DỤNG ===");
  Serial.println("test    - Bắt đầu gửi 20 gói dữ liệu");
  Serial.println("status  - Xem trạng thái hệ thống");
  Serial.println("help    - Hiển thị hướng dẫn này");
  Serial.println("reset   - Reset dữ liệu và dừng test");
  Serial.println("========================================");
}

void resetData() {
  testMode = false;
  packetCount = 0;
  baseTemp = 25.0;
  baseHumidity = 60.0;
  Serial.println("Đã reset dữ liệu!");
}