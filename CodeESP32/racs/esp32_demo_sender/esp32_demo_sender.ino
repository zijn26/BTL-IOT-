/*
 * ESP32 DHT11 Sensor Data Sender
 * Gửi dữ liệu thật từ cảm biến DHT11 lên MQTT Broker và CoAP Server
 * 
 * Yêu cầu:
 * - Thư viện: WiFi, PubSubClient, ArduinoJson, DHT
 * - Cảm biến: DHT11 kết nối vào pin 19
 * - Kết nối: WiFi
 * 
 * Cách sử dụng:
 * - Kết nối cảm biến DHT11 vào pin 19
 * - Gõ "test" vào Serial Monitor để bắt đầu gửi 20 gói dữ liệu
 * - Không gõ gì thì ESP32 sẽ không làm gì
 */

#include <WiFi.h>
#include <PubSubClient.h> // mqtt server
#include <ArduinoJson.h>
#include <WiFiUDP.h>
#include "time.h"
#include <DHT.h>

#define DHTPIN 19
#define DHTTYPE DHT11
// ==================== CẤU HÌNH ====================
// WiFi settings - THAY ĐỔI THEO MẠNG CỦA BẠN
const char* ssid = "S25+";
const char* password = "16161616";

// Server settings - THAY ĐỔI IP THEO MÁY CHẠY TestMQTT.py
const char* mqtt_server = "10.181.159.56";  // IP của máy chạy TestMQTT.py
const int mqtt_port = 20904;
const char* coap_server = "10.181.159.56";  // IP của máy chạy TestMQTT.py  
const int coap_port = 2606;

// NTP settings
const char* ntpServer = "pool.ntp.org";

// MQTT settings
const char* mqtt_topic = "test/demo";
const char* mqtt_client_id = "esp32_demo";
String subscribed_topic = ""; // Topic đã đăng ký

// CoAP settings
const char* coap_path = "/test/demo";

// ==================== BIẾN TOÀN CỤC ====================
WiFiClient espClient;
WiFiUDP udp;
PubSubClient mqttClient(espClient);
DHT dht(DHTPIN, DHTTYPE);

bool testMode = false;
bool continuousMode = false;
int packetCount = 0;
const int MAX_PACKETS = 20;
unsigned long lastPacketTime = 0;
const unsigned long TEST_INTERVAL = 2000; // 2 giây cho test mode (DHT11 cần thời gian đọc)
const unsigned long CONTINUOUS_INTERVAL = 2000; // 200ms cho chế độ liên tục

// Dữ liệu cảm biến thật
float temperature = 0.0;
float humidity = 0.0;

// Biến để theo dõi đồng bộ thời gian
bool ntpSynced = false;
unsigned long lastNtpCheck = 0;

// ==================== SETUP ====================
void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("========================================");
  Serial.println("ESP32 DHT11 Sensor Data Sender");
  Serial.println("========================================");
  Serial.println("Hướng dẫn sử dụng:");
  Serial.println("1. Cấu hình WiFi và IP server trong code");
  Serial.println("2. Kết nối cảm biến DHT11 vào pin 19");
  Serial.println("3. Gõ 'test' để gửi 20 gói dữ liệu test");
  Serial.println("4. Gõ 'batdau' để bắt đầu thu thập liên tục");
  Serial.println("5. Gõ 'dung' để dừng thu thập liên tục");
  Serial.println("6. Gõ 'sub topicname' để đăng ký topic MQTT");
  Serial.println("7. Không gõ gì thì ESP32 sẽ không làm gì");
  Serial.println("========================================");
  
  // Khởi tạo cảm biến DHT11
  dht.begin();
  Serial.println("Cảm biến DHT11 đã được khởi tạo");
  
  // Kết nối WiFi
  connectToWiFi();
  
  // Kết nối MQTT
  mqttClient.setServer(mqtt_server, mqtt_port);
  mqttClient.setCallback(mqttCallback);
  connectToMQTT();
  
  // Cấu hình NTP time với timezone UTC (để đồng bộ với server)
  configTime(0, 0, ntpServer);
  
  // Đợi đồng bộ thời gian
  Serial.println("Đang đồng bộ thời gian NTP...");
  struct tm timeinfo;
  int attempts = 0;
  while (!getLocalTime(&timeinfo) && attempts < 20) {
    delay(1000);
    attempts++;
    Serial.print(".");
  }
  if (attempts < 20) {
    Serial.println();
    Serial.println("NTP đồng bộ thành công!");
    ntpSynced = true;
  } else {
    Serial.println();
    Serial.println("NTP đồng bộ thất bại!");
    ntpSynced = false;
  }

  
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
  
  // Kiểm tra đồng bộ NTP định kỳ
  if (millis() - lastNtpCheck > 30000) { // Kiểm tra mỗi 30 giây
    checkNtpSync();
    lastNtpCheck = millis();
  }

  // Nếu đang trong chế độ test (20 gói)
  if (testMode) {
    if (packetCount < MAX_PACKETS) {
      if (millis() - lastPacketTime >= TEST_INTERVAL) {
        sendDemoData();
        lastPacketTime = millis();
        packetCount++;
      }
    } else {
      // Hoàn thành gửi 20 gói
      testMode = false;
      packetCount = 0;
      Serial.println("========================================");
      Serial.println("Đã gửi xong 20 gói dữ liệu test!");
      Serial.println("Gõ 'test' để gửi lại hoặc 'batdau' để thu thập liên tục");
      Serial.println("========================================");
    }
  }
  
  // Nếu đang trong chế độ liên tục
  if (continuousMode) {
    if (millis() - lastPacketTime >= CONTINUOUS_INTERVAL) {
      sendDemoData();
      lastPacketTime = millis();
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
      if (!testMode && !continuousMode) {
        testMode = true;
        packetCount = 0;
        lastPacketTime = 0;
        Serial.println("========================================");
        Serial.println("Bắt đầu gửi 20 gói dữ liệu test từ DHT11...");
        Serial.println("========================================");
      } else {
        Serial.println("Đang trong quá trình gửi dữ liệu, vui lòng đợi!");
      }
    } else if (input == "batdau") {
      if (!testMode && !continuousMode) {
        continuousMode = true;
        lastPacketTime = 0;
        Serial.println("========================================");
        Serial.println("Bắt đầu thu thập dữ liệu liên tục từ DHT11...");
        Serial.println("Gõ 'dung' để dừng");
        Serial.println("========================================");
      } else {
        Serial.println("Đang trong quá trình gửi dữ liệu, vui lòng đợi!");
      }
    } else if (input == "dung") {
      if (continuousMode) {
        continuousMode = false;
        Serial.println("========================================");
        Serial.println("Đã dừng thu thập dữ liệu liên tục!");
        Serial.println("========================================");
      } else {
        Serial.println("Không có chế độ liên tục nào đang chạy!");
      }
    } else if (input.startsWith("sub ")) {
      // Lệnh đăng ký topic: sub topicmuondangki
      String topic = input.substring(4); // Bỏ "sub " ở đầu
      topic.trim();
      if (topic.length() > 0) {
        subscribeToTopic(topic);
      } else {
        Serial.println("========================================");
        Serial.println("❌ Vui lòng nhập topic!");
        Serial.println("Ví dụ: sub mytopic/sensor");
        Serial.println("========================================");
      }
    } else if (input == "status") {
      printStatus();
    } else if (input == "help") {
      printHelp();
    } else if (input == "reset") {
      resetData();
    } else {
      Serial.println("Gõ 'test' để gửi 20 gói test");
      Serial.println("Gõ 'batdau' để thu thập liên tục");
      Serial.println("Gõ 'dung' để dừng thu thập");
      Serial.println("Gõ 'sub topicname' để đăng ký topic");
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
  // Tạo string từ payload
  String message = "";
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  
  // Hiển thị thông tin nhận được
  Serial.println("========================================");
  Serial.println("📨 NHẬN TIN NHẮN MQTT:");
  Serial.printf("Topic: %s\n", topic);
  Serial.printf("Message: %s\n", message.c_str());
  Serial.printf("Length: %d bytes\n", length);
  Serial.println("========================================");
}

// ==================== ĐĂNG KÝ TOPIC MQTT ====================
void subscribeToTopic(String topic) {
  if (mqttClient.connected()) {
    if (mqttClient.subscribe(topic.c_str())) {
      subscribed_topic = topic;
      Serial.println("========================================");
      Serial.printf("✅ Đã đăng ký topic: %s\n", topic.c_str());
      Serial.println("========================================");
    } else {
      Serial.println("========================================");
      Serial.printf("❌ Lỗi đăng ký topic: %s\n", topic.c_str());
      Serial.println("========================================");
    }
  } else {
    Serial.println("========================================");
    Serial.println("❌ MQTT chưa kết nối!");
    Serial.println("========================================");
  }
}

// ==================== GỬI DỮ LIỆU CẢM BIẾN ====================
void sendDemoData() {
  // Đọc dữ liệu từ cảm biến DHT11
  float temp = dht.readTemperature();
  float hum = dht.readHumidity();
  
  // Kiểm tra dữ liệu có hợp lệ không
  if (isnan(temp) || isnan(hum)) {
    Serial.println("Lỗi đọc cảm biến DHT11!");
    return;
  }
  
  // Cập nhật dữ liệu toàn cục
  temperature = temp;
  humidity = hum;
  
  // Get precise timestamp with microsecond accuracy using gettimeofday
  // Lưu ý: gettimeofday() trả về UTC time để đồng bộ với server Python
  struct timeval tv;
  gettimeofday(&tv, NULL);
  
  // tv.tv_sec  = số giây từ 1970 (UTC)
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
  doc["data"] = round(temperature * 100.0) / 100.0;                   // Nhiệt độ từ DHT11
  doc["timestamp_ms"] = timestamp_ms;           // timestamp với độ chính xác mili giây
  doc["timestamp_us"] = timestamp_us;           // timestamp với độ chính xác micro giây
  doc["humidity"] = round(humidity * 100.0) / 100.0;  // Độ ẩm từ DHT11
  doc["sensor"] = "DHT11";
  
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
  Serial.printf("[%d/%d] DHT11 - Temp: %.2f°C, Humidity: %.2f%% | Time: %s | TS_ms: %llu\n", 
                packetCount + 1, MAX_PACKETS, temperature, humidity, timeStr, timestamp_ms);
}

// ==================== GỬI DỮ LIỆU COAP ====================
int addOption(uint8_t *packet, int index, uint16_t optNum, uint16_t &lastOption,
              const uint8_t *value, uint8_t length) {
  uint16_t delta = optNum - lastOption;
  if(delta >= 13 && length< 13 ) {
    packet[index++] = (13 << 4) | (length & 0x0F);
    packet[index++] = (delta - 13) & 0xFF;
  }else {
      packet[index++] = (delta << 4) | (length & 0x0F);
  }
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
  uint8_t t   = 0;       // type 
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
  Serial.printf("Subscribed Topic: %s\n", subscribed_topic.length() > 0 ? subscribed_topic.c_str() : "None");
  Serial.printf("NTP Sync: %s\n", ntpSynced ? "OK" : "FAILED");
  Serial.printf("Test Mode: %s\n", testMode ? "ON" : "OFF");
  Serial.printf("Continuous Mode: %s\n", continuousMode ? "ON" : "OFF");
  Serial.printf("Packets Sent: %d/%d\n", packetCount, MAX_PACKETS);
  Serial.printf("Current Temp: %.1f°C\n", temperature);
  Serial.printf("Current Humidity: %.1f%%\n", humidity);
  
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
  Serial.println("test    - Gửi 20 gói dữ liệu test (2s/gói)");
  Serial.println("batdau  - Bắt đầu thu thập liên tục (2s/gói)");
  Serial.println("dung    - Dừng thu thập liên tục");
  Serial.println("sub topicname - Đăng ký topic MQTT");
  Serial.println("status  - Xem trạng thái hệ thống");
  Serial.println("help    - Hiển thị hướng dẫn này");
  Serial.println("reset   - Reset dữ liệu và dừng tất cả");
  Serial.println("========================================");
}

void resetData() {
  testMode = false;
  continuousMode = false;
  packetCount = 0;
  temperature = 0.0;
  humidity = 0.0;
  Serial.println("Đã reset dữ liệu và dừng tất cả chế độ!");
}

// ==================== KIỂM TRA ĐỒNG BỘ NTP ====================
void checkNtpSync() {
  struct tm timeinfo;
  if (getLocalTime(&timeinfo)) {
    if (!ntpSynced) {
      Serial.println("NTP đã được đồng bộ!");
      ntpSynced = true;
    }
  } else {
    if (ntpSynced) {
      Serial.println("CẢNH BÁO: Mất đồng bộ NTP!");
      ntpSynced = false;
    }
  }
}