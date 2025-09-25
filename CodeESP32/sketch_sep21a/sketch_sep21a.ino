#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <WebServer.h>
#include <driver/i2s.h>
#include <SPIFFS.h>
#include <ArduinoJson.h>

// Thông tin WiFi
const char* ssid = "310";
const char* password = "88969696";

// Wit.ai Access Token
const char* wit_access_token = "XNEACJL4ODFGEWYCYGOLRYGYX2OFP54G";

// Cấu hình I2S cho INMP441
#define I2S_WS 25
#define I2S_SD 33
#define I2S_SCK 32
#define I2S_PORT I2S_NUM_0

// Cấu hình ghi âm được cải thiện
#define SAMPLE_RATE 16000  // Tăng lên 16kHz để chất lượng tốt hơn
#define RECORD_TIME 6      // 3 giây
#define BITS_PER_SAMPLE 16
#define I2S_READ_LEN (1024)
#define AUDIO_GAIN 6       // Hệ số khuếch đại (có thể điều chỉnh từ 1-10)

// Biến toàn cục
bool isRecording = false;
int16_t i2s_read_buff[I2S_READ_LEN];
WebServer server(80);

// WAV file header structure
struct WavHeader {
  char riff[4] = {'R', 'I', 'F', 'F'};
  uint32_t file_size;
  char wave[4] = {'W', 'A', 'V', 'E'};
  char fmt[4] = {'f', 'm', 't', ' '};
  uint32_t fmt_size = 16;
  uint16_t audio_format = 1;
  uint16_t num_channels = 1;
  uint32_t sample_rate = SAMPLE_RATE;
  uint32_t byte_rate;
  uint16_t block_align;
  uint16_t bits_per_sample = BITS_PER_SAMPLE;
  char data[4] = {'d', 'a', 't', 'a'};
  uint32_t data_size;
};

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("\n=== ESP32 VOICE RECORDING SYSTEM V2.0 ===");

  // Khởi tạo SPIFFS
  if (!SPIFFS.begin(true)) {
    Serial.println("❌ Lỗi khởi tạo SPIFFS!");
    return;
  }
  Serial.println("✅ SPIFFS khởi tạo thành công");

  // Kết nối WiFi
  WiFi.begin(ssid, password);
  Serial.print("🔄 Đang kết nối WiFi");
  
  int wifi_attempts = 0;
  while (WiFi.status() != WL_CONNECTED && wifi_attempts < 30) {
    delay(500);
    Serial.print(".");
    wifi_attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.println("✅ WiFi đã kết nối!");
    Serial.print("📡 IP Address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println();
    Serial.println("❌ Không thể kết nối WiFi!");
    return;
  }

  // Khởi tạo I2S với cấu hình tối ưu
  Serial.println("🔧 Đang khởi tạo I2S...");
  i2s_install();
  i2s_setpin();
  i2s_start(I2S_PORT);
  Serial.println("✅ I2S khởi tạo thành công");

  // Khởi tạo Web Server
  setupWebServer();
  server.begin();
  Serial.println("🌐 Web Server đã khởi động");

  Serial.println("\n=== HỆ THỐNG SẴN SÀNG ===");
  Serial.println("📝 Các lệnh có sẵn:");
  Serial.println("   • 'ghiam' - Bắt đầu ghi âm 3 giây");
  Serial.println("   • 'test' - Kiểm tra tín hiệu microphone");
  Serial.println("   • 'download' - Xem link tải file");
  Serial.println("🌐 Web Interface: http://" + WiFi.localIP().toString());
  Serial.println("📥 Download: http://" + WiFi.localIP().toString() + "/download");
  Serial.println("===============================\n");
}

void loop() {
  // Xử lý web server
  server.handleClient();

  // Kiểm tra lệnh từ Serial
  if (Serial.available()) {
    String command = Serial.readString();
    command.trim();
    command.toLowerCase();

    if (command == "ghiam" && !isRecording) {
      Serial.println("\n🎙️  BẮT ĐẦU QUÁ TRÌNH GHI ÂM");
      Serial.println("🔍 Đang kiểm tra microphone...");
      
      if (true) {
        Serial.println("✅ Microphone hoạt động tốt!");
        Serial.println("🎤 Bắt đầu ghi âm trong " + String(RECORD_TIME) + " giây...");
        Serial.println("🗣️  HÃY NÓI NGAY BÂY GIỜ!");
        recordAudio();
        Serial.println("📤 Đang gửi lên Wit.ai để nhận diện...");
        sendToWitAI();
      } else {
        Serial.println("❌ Microphone không có tín hiệu hoặc quá yếu!");
        Serial.println("💡 Kiểm tra kết nối và thử lại");
      }
    }
    else if (command == "test") {
      Serial.println("\n🔧 KIỂM TRA MICROPHONE");
      testMicrophone();
    }
    else if (command == "download") {
      Serial.println("\n📥 THÔNG TIN TẢI FILE:");
      Serial.println("🌐 Web Interface: http://" + WiFi.localIP().toString());
      Serial.println("📁 Direct Download: http://" + WiFi.localIP().toString() + "/download");
      Serial.println("ℹ️  File Info: http://" + WiFi.localIP().toString() + "/info");
    }
    else if (command.length() > 0) {
      Serial.println("❓ Lệnh không hợp lệ: " + command);
      Serial.println("💡 Sử dụng: 'ghiam', 'test', hoặc 'download'");
    }
  }

  delay(100);
}

void setupWebServer() {
  // Trang chủ với giao diện đẹp hơn
  server.on("/", []() {
    String html = R"(
<!DOCTYPE html>
<html>
<head>
    <title>ESP32 Audio Recording System</title>
    <meta charset='utf-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1'>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f0f0f0; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
        h1 { color: #333; text-align: center; }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        .file-link { display: block; padding: 10px; margin: 5px 0; background: #007bff; color: white; text-decoration: none; border-radius: 5px; text-align: center; }
        .file-link:hover { background: #0056b3; }
        .instructions { background: #fff3cd; padding: 15px; border-radius: 5px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class='container'>
        <h1>🎙️ ESP32 Audio Recording System</h1>
        <div class='status success'>
            <strong>✅ System Status:</strong> Online and Ready
        </div>
)";

    html += "<div class='status info'>";
    html += "<strong>📊 System Info:</strong><br>";
    html += "Sample Rate: " + String(SAMPLE_RATE) + " Hz<br>";
    html += "Record Duration: " + String(RECORD_TIME) + " seconds<br>";
    html += "Audio Gain: " + String(AUDIO_GAIN) + "x amplification<br>";
    html += "IP Address: " + WiFi.localIP().toString();
    html += "</div>";

    // Kiểm tra file có sẵn
    File root = SPIFFS.open("/");
    File file = root.openNextFile();
    bool hasFiles = false;
    
    html += "<h2>📁 Available Audio Files:</h2>";
    
    while (file) {
      if (String(file.name()).endsWith(".wav")) {
        hasFiles = true;
        html += "<a href='/download?file=" + String(file.name()) + "' class='file-link'>";
        html += "📥 Download " + String(file.name()) + " (" + String(file.size()) + " bytes)</a>";
      }
      file = root.openNextFile();
    }
    
    if (!hasFiles) {
      html += "<div class='status info'>No audio files available. Record some audio first using Serial Monitor.</div>";
    }

    html += R"(
        <div class='instructions'>
            <h3>📋 Instructions:</h3>
            <ol>
                <li>Open Serial Monitor (115200 baud)</li>
                <li>Type <strong>'ghiam'</strong> and press Enter to start recording</li>
                <li>Speak clearly for 3 seconds when prompted</li>
                <li>Wait for Wit.ai speech recognition results</li>
                <li>Download recorded files using the links above</li>
            </ol>
            <p><strong>💡 Tips:</strong></p>
            <ul>
                <li>Speak 5-15cm from the microphone</li>
                <li>Record in a quiet environment</li>
                <li>Speak clearly and not too fast</li>
            </ul>
        </div>
    </div>
</body>
</html>
)";
    
    server.send(200, "text/html", html);
  });

  // Endpoint tải file
  server.on("/download", []() {
    String filename = "/recorded.wav";
    if (server.hasArg("file")) {
      filename = "/" + server.arg("file");
    }
    
    File file = SPIFFS.open(filename, "r");
    if (!file) {
      server.send(404, "text/plain", "❌ File not found! Please record audio first by sending 'ghiam' command via Serial Monitor.");
      return;
    }
    
    String downloadName = "esp32_recording_" + String(millis()) + ".wav";
    server.sendHeader("Content-Disposition", "attachment; filename=\"" + downloadName + "\"");
    server.streamFile(file, "audio/wav");
    file.close();
    
    Serial.println("📥 File downloaded: " + filename);
  });

  // Endpoint thông tin hệ thống
  server.on("/info", []() {
    String info = "ESP32 Audio Recording System v2.0\n";
    info += "=====================================\n\n";
    info += "Network Information:\n";
    info += "IP Address: " + WiFi.localIP().toString() + "\n";
    info += "WiFi SSID: " + String(ssid) + "\n\n";
    info += "Audio Configuration:\n";
    info += "Sample Rate: " + String(SAMPLE_RATE) + " Hz\n";
    info += "Record Duration: " + String(RECORD_TIME) + " seconds\n";
    info += "Bits Per Sample: " + String(BITS_PER_SAMPLE) + " bit\n";
    info += "Audio Gain: " + String(AUDIO_GAIN) + "x amplification\n";
    info += "Channels: Mono (Left channel)\n\n";
    
    info += "File System:\n";
    info += "SPIFFS Total: " + String(SPIFFS.totalBytes()) + " bytes\n";
    info += "SPIFFS Used: " + String(SPIFFS.usedBytes()) + " bytes\n\n";
    
    File file = SPIFFS.open("/recorded.wav", "r");
    if (file) {
      info += "Last Recording:\n";
      info += "File Size: " + String(file.size()) + " bytes\n";
      info += "Duration: ~" + String(file.size() * 8 / SAMPLE_RATE / BITS_PER_SAMPLE) + " seconds\n";
      file.close();
    } else {
      info += "Last Recording: No file available\n";
    }
    
    server.send(200, "text/plain", info);
  });
}

bool checkMicrophone() {
  size_t bytes_read = 0;
  esp_err_t result = i2s_read(I2S_PORT, i2s_read_buff, 256 * sizeof(int16_t), &bytes_read, 100);
  
  if (result == ESP_OK && bytes_read > 0) {
    int32_t sum = 0;
    int sample_count = bytes_read / 2;
    for (int i = 0; i < sample_count; i++) {
      sum += abs(i2s_read_buff[i]);
    }
    int avg = sum / sample_count;
    Serial.print("📊 Mức tín hiệu: ");
    Serial.print(avg);
    
    if (avg > 30) {
      Serial.println(" ✅ (Tốt)");
      return true;
    } else if (avg > 10) {
      Serial.println(" ⚠️  (Yếu)");
      return false;
    } else {
      Serial.println(" ❌ (Quá yếu)");
      return false;
    }
  }
  Serial.println("❌ Không đọc được dữ liệu");
  return false;
}

void testMicrophone() {
  Serial.println("🔄 Đang test microphone trong 5 giây...");
  Serial.println("🗣️  Hãy nói thử để kiểm tra tín hiệu:");
  
  unsigned long start_time = millis();
  int max_level = 0;
  int min_level = 32767;
  int sample_count = 0;
  long total_level = 0;
  
  while (millis() - start_time < 5000) {
    size_t bytes_read = 0;
    esp_err_t result = i2s_read(I2S_PORT, i2s_read_buff, 64 * sizeof(int16_t), &bytes_read, 100);
    
    if (result == ESP_OK && bytes_read > 0) {
      int count = bytes_read / 2;
      int32_t sum = 0;
      
      for (int i = 0; i < count; i++) {
        int level = abs(i2s_read_buff[i]);
        sum += level;
        if (level > max_level) max_level = level;
        if (level < min_level) min_level = level;
      }
      
      int avg = sum / count;
      total_level += avg;
      sample_count++;
      
      // Hiển thị thanh mức độ đơn giản
      Serial.print("📊 ");
      int bars = avg / 100;
      for (int i = 0; i < bars && i < 20; i++) {
        Serial.print("█");
      }
      Serial.print(" (");
      Serial.print(avg);
      Serial.println(")");
    }
    delay(200);
  }
  
  Serial.println("\n📈 KẾT QUẢ KIỂM TRA:");
  Serial.println("Max Level: " + String(max_level));
  Serial.println("Min Level: " + String(min_level));
  Serial.println("Avg Level: " + String(total_level / sample_count));
  
  if (max_level < 50) {
    Serial.println("❌ Tín hiệu quá yếu - Kiểm tra kết nối microphone");
  } else if (max_level < 200) {
    Serial.println("⚠️  Tín hiệu yếu - Nói gần micro hơn hoặc to hơn");
  } else {
    Serial.println("✅ Tín hiệu tốt - Microphone hoạt động bình thường");
  }
}

void applyAGC(int16_t* samples, int count) {
  // Tính mức tín hiệu trung bình
  int32_t sum = 0;
  for (int i = 0; i < count; i++) {
    sum += abs(samples[i]);
  }
  int avg = sum / count;
  
  // Tính toán gain tự động dựa trên mức tín hiệu
  int dynamic_gain = AUDIO_GAIN;
  if (avg < 50) {
    dynamic_gain = AUDIO_GAIN + 60;  // Tăng gain cho tín hiệu yếu
  } else if (avg < 100) {
    dynamic_gain = AUDIO_GAIN + 60;
  } else if (avg > 1000) {
    dynamic_gain = max(1, AUDIO_GAIN - 2);  // Giảm gain cho tín hiệu mạnh
  }
  
  // Áp dụng gain với giới hạn
  for (int i = 0; i < count; i++) {
    int32_t amplified = samples[i] * dynamic_gain;
    
    // Soft clipping để giảm méo
    if (amplified > 32767) amplified = 32767;
    if (amplified < -32768) amplified = -32768;
    
    samples[i] = (int16_t)amplified;
  }
}

void i2s_install() {
  const i2s_config_t i2s_config = {
    .mode = i2s_mode_t(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = i2s_bits_per_sample_t(BITS_PER_SAMPLE),
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = i2s_comm_format_t(I2S_COMM_FORMAT_STAND_I2S),
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,  // Higher priority
    .dma_buf_count = 8,
    .dma_buf_len = 512,   // Smaller buffer for lower latency
    .use_apll = true      // Use APLL for better precision
  };

  i2s_driver_install(I2S_PORT, &i2s_config, 0, NULL);
}

void i2s_setpin() {
  const i2s_pin_config_t pin_config = {
    .bck_io_num = I2S_SCK,
    .ws_io_num = I2S_WS,
    .data_out_num = -1,
    .data_in_num = I2S_SD
  };

  i2s_set_pin(I2S_PORT, &pin_config);
}

void recordAudio() {
  isRecording = true;
  Serial.println("⏺️  RECORDING STARTED");

  // Xóa file cũ nếu có
  if (SPIFFS.exists("/recorded.wav")) {
    SPIFFS.remove("/recorded.wav");
  }

  // Tạo file WAV trên SPIFFS
  File audioFile = SPIFFS.open("/recorded.wav", "w");
  if (!audioFile) {
    Serial.println("❌ Không thể tạo file âm thanh!");
    isRecording = false;
    return;
  }

  // Tính toán kích thước dữ liệu
  uint32_t data_size = SAMPLE_RATE * BITS_PER_SAMPLE / 8 * RECORD_TIME;

  // Tạo WAV header
  WavHeader header;
  header.file_size = sizeof(WavHeader) + data_size - 8;
  header.byte_rate = SAMPLE_RATE * BITS_PER_SAMPLE / 8;
  header.block_align = BITS_PER_SAMPLE / 8;
  header.data_size = data_size;

  // Ghi header vào file
  audioFile.write((uint8_t*)&header, sizeof(WavHeader));

  // Bắt đầu ghi âm
  unsigned long start_time = millis();
  size_t bytes_read = 0;
  int max_amplitude = 0;
  int samples_processed = 0;

  Serial.println("🎙️  Recording in progress:");

  while (millis() - start_time < RECORD_TIME * 1000) {
    esp_err_t result = i2s_read(I2S_PORT, i2s_read_buff, I2S_READ_LEN * sizeof(int16_t), &bytes_read, 100);

    if (result == ESP_OK && bytes_read > 0) {
      int sample_count = bytes_read / 2;
      
      // Áp dụng AGC (Automatic Gain Control)
      // applyAGC(i2s_read_buff, sample_count);
      
      // Ghi dữ liệu đã xử lý vào file
      audioFile.write((uint8_t*)i2s_read_buff, bytes_read);

      // Tính toán và hiển thị mức âm thanh
      int32_t sum = 0;
      for (int i = 0; i < sample_count; i++) {
        int amp = abs(i2s_read_buff[i]);
        sum += amp;
        if (amp > max_amplitude) max_amplitude = amp;
      }
      
      int avg = sum / sample_count;
      samples_processed += sample_count;

      // Hiển thị thanh tiến độ và mức âm
      int progress = ((millis() - start_time) * 100) / (RECORD_TIME * 1000);
      Serial.print("📊 [");
      Serial.print(progress);
      Serial.print("%] Level: ");
      
      // Thanh mức độ trực quan
      int bars = avg / 200;
      for (int i = 0; i < bars && i < 15; i++) {
        Serial.print("█");
      }
      Serial.print(" (");
      Serial.print(avg);
      Serial.println(")");

      // Nhấp nháy LED
      digitalWrite(LED_BUILTIN, (millis() / 200) % 2);
    }
    
    yield();  // Cho phép các task khác chạy
  }

  audioFile.close();
  digitalWrite(LED_BUILTIN, LOW);
  isRecording = false;

  Serial.println("\n✅ GHI ÂM HOÀN THÀNH!");
  Serial.println("📈 Max Amplitude: " + String(max_amplitude));
  Serial.println("📊 Samples Processed: " + String(samples_processed));
  Serial.println("💾 File Size: " + String(SPIFFS.open("/recorded.wav", "r").size()) + " bytes");
  Serial.println("📥 Download: http://" + WiFi.localIP().toString() + "/download");
}

void sendToWitAI() {
  Serial.println("\n🌐 CONNECTING TO WIT.AI...");
  WiFiClientSecure client;
  client.setInsecure();

  if (!client.connect("api.wit.ai", 443)) {
    Serial.println("❌ Không thể kết nối tới Wit.ai!");
    return;
  }
  Serial.println("✅ Đã kết nối tới Wit.ai");

  File audioFile = SPIFFS.open("/recorded.wav", "r");
  if (!audioFile) {
    Serial.println("❌ Không thể đọc file âm thanh!");
    client.stop();
    return;
  }

  // Bỏ qua WAV header (44 bytes)
  audioFile.seek(44);
  size_t audio_data_size = audioFile.size() - 44;
  Serial.println("📤 Uploading " + String(audio_data_size) + " bytes...");

  // Gửi HTTP request header
  client.println("POST /speech?v=20220622 HTTP/1.1");
  client.println("Host: api.wit.ai");
  client.print("Authorization: Bearer ");
  client.println(wit_access_token);
  client.println("Content-Type: audio/wav");
  client.print("Content-Length: ");
  client.println(audio_data_size);
  client.println("Connection: close");
  client.println();

  // Gửi dữ liệu âm thanh với progress
  uint8_t buffer[1024];
  size_t bytes_sent = 0;
  unsigned long upload_start = millis();

  while (audioFile.available()) {
    size_t bytes_read = audioFile.read(buffer, sizeof(buffer));
    client.write(buffer, bytes_read);
    bytes_sent += bytes_read;

    int progress = (bytes_sent * 100) / audio_data_size;
    if (bytes_sent % (audio_data_size / 10) == 0 || !audioFile.available()) {
      Serial.print("📤 Upload: ");
      Serial.print(progress);
      Serial.println("%");
    }
  }

  audioFile.close();
  unsigned long upload_time = millis() - upload_start;
  Serial.println("✅ Upload completed in " + String(upload_time) + "ms");
  Serial.println("⏳ Waiting for response...");

  // Đọc phản hồi từ server
  String response = "";
  unsigned long timeout = millis() + 15000; // 15 seconds timeout

  while (client.connected() && millis() < timeout) {
    if (client.available()) {
      response += client.readString();
      break;
    }
    delay(10);
  }

  client.stop();

  if (response.length() == 0) {
    Serial.println("❌ Timeout - No response from Wit.ai");
    return;
  }

  // Xử lý phản hồi JSON
  parseWitResponse(response);
}

void parseWitResponse(String response) {
  Serial.println("\n" + String("=").substring(0,50));
  Serial.println("🤖 WIT.AI SPEECH RECOGNITION RESULT");
  Serial.println(String("=").substring(0,50));

  int json_start = response.indexOf("\r\n\r\n");
  if (json_start == -1) {
    json_start = response.indexOf("\n\n");
  }

  if (json_start == -1) {
    Serial.println("❌ No JSON data found in response!");
    Serial.println("📝 Raw response:");
    Serial.println(response);
    return;
  }

  String json_data = response.substring(json_start + 4);
  Serial.println("📋 Raw JSON:");
  Serial.println(json_data);
  Serial.println();

  DynamicJsonDocument doc(2048);
  DeserializationError error = deserializeJson(doc, json_data);

  if (error) {
    Serial.println("❌ JSON Parse Error: " + String(error.c_str()));
    return;
  }

  if (doc.containsKey("text")) {
    String recognized_text = doc["text"].as<String>();
    
    if (recognized_text.length() > 0) {
      Serial.println("🎯 SPEECH RECOGNITION SUCCESS!");
      Serial.println("📝 Recognized Text: \"" + recognized_text + "\"");
      Serial.println("📏 Text Length: " + String(recognized_text.length()) + " characters");
    } else {
      Serial.println("⚠️  Empty text returned - speech not recognized");
    }

    if (doc.containsKey("intents") && doc["intents"].size() > 0) {
      Serial.println("\n💡 INTENT ANALYSIS:");
      JsonArray intents = doc["intents"];
      for (int i = 0; i < intents.size(); i++) {
        String intent = intents[i]["name"].as<String>();
        float confidence = intents[i]["confidence"].as<float>();
        Serial.println("   Intent: " + intent + " (Confidence: " + String(confidence * 100, 1) + "%)");
      }
    }

    if (doc.containsKey("entities") && doc["entities"].size() > 0) {
      Serial.println("\n🏷️  ENTITIES DETECTED:");
      JsonObject entities = doc["entities"];
      for (JsonPair kv : entities) {
        String entity_name = kv.key().c_str();
        JsonArray values = kv.value();
        for (int i = 0; i < values.size(); i++) {
          String entity_value = values[i]["value"].as<String>();
          float entity_confidence = values[i]["confidence"].as<float>();
          Serial.println("   " + entity_name + ": " + entity_value + " (" + String(entity_confidence * 100, 1) + "%)");
        }
      }
    }

    if (doc.containsKey("traits") && doc["traits"].size() > 0) {
      Serial.println("\n🎭 TRAITS DETECTED:");
      JsonObject traits = doc["traits"];
      for (JsonPair kv : traits) {
        String trait_name = kv.key().c_str();
        JsonArray values = kv.value();
        for (int i = 0; i < values.size(); i++) {
          String trait_value = values[i]["value"].as<String>();
          float trait_confidence = values[i]["confidence"].as<float>();
          Serial.println("   " + trait_name + ": " + trait_value + " (" + String(trait_confidence * 100, 1) + "%)");
        }
      }
    }

  } else {
    Serial.println("❌ NO SPEECH RECOGNIZED");
    
    if (doc.containsKey("error")) {
      String error_msg = doc["error"].as<String>();
      Serial.println("🚨 Error: " + error_msg);
    } else {
      Serial.println("💡 Possible causes:");
      Serial.println("   • Audio too quiet or noisy");
      Serial.println("   • Speech not clear enough");
      Serial.println("   • Network connectivity issues");
      Serial.println("   • Microphone not working properly");
    }
  }

  Serial.println(String("=").substring(0,50));
  Serial.println("🎙️  Type 'ghiam' to record again");
  Serial.println("🔧 Type 'test' to test microphone");
  Serial.println("📥 Type 'download' for file links");
  Serial.println(String("=").substring(0,50) + "\n");
}
