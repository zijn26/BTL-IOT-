#include <WiFi.h>
#include <HTTPClient.h>
#include "DHT.h"

#define DHTPIN 4       // GPIO4
#define DHTTYPE DHT11  // hoặc DHT22

DHT dht(DHTPIN, DHTTYPE);

const char* ssid = "TaoManhDuc";
const char* password = "02092606";

// ==== API Key của Write Channel ====
String apiKey = "42TSZMO8OXWIOMT5";

void setup() {
  Serial.begin(115200);
  dht.begin();

  WiFi.begin(ssid, password);
  Serial.print("🔌 Đang kết nối WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ Kết nối WiFi thành công!");
  Serial.print("📡 Địa chỉ IP ESP32: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    float h = dht.readHumidity();
    float t = dht.readTemperature();

    if (isnan(h) || isnan(t)) {
      Serial.println("⚠️ Lỗi đọc cảm biến DHT!");
      return;
    }

    // HTTPClient http;
    // String url = "http://api.thingspeak.com/update?api_key=" + apiKey +
    //              "&field1=" + String(t) + "&field2=" + String(h);

    // Serial.println("📤 Gửi dữ liệu tới: " + url);

    // http.begin(url);
    // int httpCode = http.GET();

    String postData = "api_key=" + apiKey + "&field1=" + String(t) + "&field2=" + String(h);

    http.begin("http://api.thingspeak.com/update");
    http.addHeader("Content-Type", "application/x-www-form-urlencoded");

    int httpCode = http.POST(postData);

    // String plainData = apiKey + "\n" + String(t) + "\n" + String(h);

    // http.begin("http://api.thingspeak.com/update");
    // http.addHeader("Content-Type", "text/plain");

    // int httpCode2 = http.POST(plainData);


    Serial.println("📤 Gửi POST (form-urlencoded): " + postData);

    if (httpCode > 0) {
      Serial.printf("✅ HTTP Response code: %d\n", httpCode);
      String payload = http.getString();
      Serial.println("📩 Server trả về: " + payload);
    } else {
      Serial.printf("❌ Lỗi request: %s\n", http.errorToString(httpCode).c_str());
    }
    http.end();
  }

  delay(20000); // gửi mỗi 20s (ThingSpeak yêu cầu ≥15s/lần)
}
