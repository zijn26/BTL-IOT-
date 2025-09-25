#include <WiFi.h>
#include <HTTPClient.h>

// ==== Thông tin WiFi ====
const char* ssid = "TaoManhDuc";
const char* password = "02092606";

// ==== API Key & Thông tin OpenWeather ====
String apiKey = "87891791ee47c1fd26e3a447ed73c69a";   // 🔑 thay bằng API key của bạn
String lat = "21.0285";           // Vĩ độ Hà Nội
String lon = "105.8542";          // Kinh độ Hà Nội
String units = "metric";          // metric = °C

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);

  Serial.print("🔌 Đang kết nối WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ Đã kết nối WiFi");
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    WiFiClient client;

    // ==== URL Weather API (2.5) ====
    String url = "http://api.openweathermap.org/data/2.5/weather?lat=" 
                 + lat + "&lon=" + lon 
                 + "&appid=" + apiKey + "&units=" + units;

    Serial.println("📡 Gửi request: " + url);

    http.begin(client, url); 
    int httpCode = http.GET(); 

    if (httpCode > 0) {
      Serial.printf("📩 HTTP code: %d\n", httpCode);
      if (httpCode == HTTP_CODE_OK) {
        String payload = http.getString();
        Serial.println("🌦️ Dữ liệu thời tiết:");
        Serial.println(payload);
      }
    } else {
      Serial.printf("❌ Lỗi request: %s\n", http.errorToString(httpCode).c_str());
    }

    http.end();
  } else {
    Serial.println("⚠️ Mất kết nối WiFi");
  }

  delay(60000); // Gọi API mỗi 60 giây
}
