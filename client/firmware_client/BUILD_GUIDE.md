# 📚 Hướng Dẫn Build và Flash ESP32 qua Arduino IDE

## 🎯 Yêu cầu hệ thống

### 1. Phần mềm cần cài đặt
- **Arduino IDE** phiên bản 1.8.19 trở lên hoặc **Arduino IDE 2.x**
- **ESP32 Board Support** (cài qua Board Manager)

### 2. Thư viện cần cài đặt

#### Arduino IDE 1.8.x:
1. Vào `Tools` → `Board` → `Boards Manager`
2. Tìm kiếm `esp32` bởi Espressif Systems
3. Cài đặt phiên bản **2.0.11** trở lên

#### Arduino IDE 2.x:
1. Vào `Tools` → `Board` → `Boards Manager`
2. Tìm kiếm `esp32` bởi Espressif Systems  
3. Cài đặt phiên bản **2.0.11** trở lên

### 3. Thư viện bổ sung (KHÔNG CẦN)
- Tất cả thư viện cần thiết đã có sẵn trong ESP32 core
- WiFi, WebServer, PubSubClient đều được tích hợp

---

## 🔧 Cấu hình Arduino IDE

### 1. Cài đặt ESP32 Board

**Arduino IDE 1.8.x:**
```
File → Preferences → Additional Board Manager URLs
```
Thêm URL:
```
https://espressif.github.io/arduino-esp32/package_esp32_index.json
```

**Arduino IDE 2.x:**
```
File → Preferences → Settings → Additional Board Manager URLs
```
Thêm URL:
```
https://espressif.github.io/arduino-esp32/package_esp32_index.json
```

### 2. Cài Board ESP32
1. Vào `Tools` → `Board` → `Boards Manager`
2. Gõ `esp32` vào ô tìm kiếm
3. Chọn **esp32 by Espressif Systems**
4. Click `Install` (phiên bản 2.0.11 trở lên)
5. Chờ cài đặt hoàn tất (5-10 phút)

---

## 📦 Cấu trúc thư mục

Đảm bảo cấu trúc thư mục như sau:
```
CodeESP32/SLAVE/
├── ESP32_MultiThread_IoT.ino   ← File chính (đã sửa)
├── wifiStation.h
├── wifiStation.cpp
├── settings.h
├── settings.cpp
├── mqtt.h
├── mqtt.cpp
├── gpioManager.h
├── gpioManager.cpp
├── systemConfig.h
└── README.md
```

**LƯU Ý QUAN TRỌNG:** 
- Tất cả các file `.h` và `.cpp` **PHẢI** nằm cùng thư mục với file `.ino`
- Arduino IDE sẽ tự động compile tất cả file `.cpp` và `.h` trong cùng thư mục

---

## 🚀 Các bước Build và Flash

### Bước 1: Mở Project
1. Khởi động **Arduino IDE**
2. Mở file: `File → Open → ESP32_MultiThread_IoT.ino`
3. Đảm bảo tất cả file .h và .cpp đều mở (xem tab phía trên)

### Bước 2: Chọn Board và Port

**Chọn Board:**
```
Tools → Board → ESP32 Arduino → ESP32 Dev Module
```

**Chọn Port:**
```
Tools → Port → COMx (Windows) hoặc /dev/ttyUSB0 (Linux)
```

**Kiểm tra Port có dấu**: 
- Trên Windows: Device Manager → Ports (COM & LPT)
- Trên Linux: `ls /dev/ttyUSB*`

### Bước 3: Cấu hình Build Options

```
Tools → Partition Scheme → Default 4MB with spiffs (3MB APP/9.9MB SPIFFS)
Tools → Upload Speed → 921600
Tools → CPU Frequency → 240MHz (WiFi/BT)
Tools → Flash Frequency → 80MHz
Tools → Flash Mode → QIO
Tools → Flash Size → 4MB (32Mb)
Tools → Upload Mode → Default (do not change)
Tools → Core Debug Level → None
```

### Bước 4: Kiểm tra cấu hình MQTT Broker

Mở file `ESP32_MultiThread_IoT.ino`, dòng 70:
```cpp
mqtt->updateConfig("192.168.1.100", 1883, CLIENT_ID);
```

**Sửa IP Broker MQTT** cho đúng với server của bạn:
- Thay `"192.168.1.100"` bằng IP MQTT Broker thực tế
- Port thường là `1883` (MQTT) hoặc `8883` (MQTTS)
- `CLIENT_ID` đã được định nghĩa ở dòng 10

### Bước 5: Build và Upload

**Cách 1: Build rồi Upload**
```
1. Sketch → Verify/Compile (Ctrl+R) - Kiểm tra lỗi compile
2. Sketch → Upload (Ctrl+U) - Flash vào ESP32
```

**Cách 2: Upload trực tiếp**
```
Sketch → Upload (Ctrl+U)
```

**Quá trình Upload:**
1. Arduino IDE sẽ compile code (30 giây - 2 phút)
2. Màn hình hiển thị "Connecting........_____..." 
3. **Nhấn nút BOOT trên ESP32** (giữ trong lúc "Connecting")
4. Màn hình hiển thị "Writing at 0x00010000..." 
5. Chờ upload (10-30 giây)
6. Hiển thị "Hard resetting via RTS pin..."
7. **Hoàn thành!**

---

## 🔍 Xử lý lỗi thường gặp

### Lỗi 1: Port không tìm thấy
**Triệu chứng:**
```
A fatal error occurred: Failed to connect to ESP32: Timed out...
```

**Giải pháp:**
1. Kiểm tra cáp USB (thử cáp khác)
2. Cài đặt Driver CP2102 hoặc CH340
3. Nhấn nút BOOT khi đang "Connecting"
4. Thử port khác trong Tools → Port

### Lỗi 2: Compile Error - Cannot find library
**Triệu chứng:**
```
fatal error: PubSubClient.h: No such file or directory
```

**Giải pháp:**
- Lỗi này **KHÔNG NÊN XẢY RA** vì PubSubClient có sẵn trong ESP32
- Đảm bảo đã chọn board "ESP32 Dev Module"
- Kiểm tra ESP32 core đã cài đặt đúng chưa

### Lỗi 3: Multiple definition
**Triệu chứng:**
```
multiple definition of 'class::method'
```

**Giải pháp:**
- Kiểm tra không có file nào bị duplicate
- Đóng tất cả tab, mở lại file `.ino`

### Lỗi 4: Upload failed at writing
**Triệu chứng:**
```
Writing at 0x1000... (0 %) ... failed!
```

**Giải pháp:**
1. Giữ nút BOOT trong khi upload
2. Giảm Upload Speed xuống **115200**
3. Thử cáp USB khác
4. Reset ESP32 (nhấn EN)

### Lỗi 5: Device not in sync
**Triệu chứng:**
```
Guru Meditation Error: Core 1 panic'ed
```

**Giải pháp:**
1. Nhấn nút EN để reset ESP32
2. Thử upload lại
3. Kiểm tra nguồn cấp (USB 2.0 có thể yếu)

---

## ✅ Kiểm tra sau khi Upload

### 1. Mở Serial Monitor
```
Tools → Serial Monitor (Ctrl+Shift+M)
```

### 2. Cấu hình Serial Monitor
```
Baud Rate: 115200
Line Ending: Both NL & CR
```

### 3. Reset ESP32
Nhấn nút **EN** (Reset) trên board

### 4. Xem Serial Output

**Kết nối WiFi thành công:**
```
🚀 Starting ESP32 Multi-Thread IoT Device...
📊 Free heap at start: 250000 bytes
✅ [Settings] NVS initialized successfully
✅ [WiFiStation] WiFi connected successfully!
✅ MQTT connected!
📡 [WiFiTask] Started on Core 0
📨 [MQTTTask] Started on Core 1
🔌 [GPIOTask] Started on Core 0
🌡️ [SensorTask] Started on Core 1
✅ All tasks created successfully!
```

**Chưa có cấu hình WiFi:**
```
📡 [WiFiStation] No WiFi config found in NVS
📡 [WiFiStation] Starting config mode...
✅ [WiFiStation] Access Point started: ESP32_Config_1234 (No Password)
📱 [WiFiStation] Connect to WiFi: ESP32_Config_1234
🌐 [WiFiStation] Open browser: http://192.168.4.1
```

---

## 🌐 Cấu hình WiFi lần đầu

Nếu ESP32 chạy ở Config Mode:

1. **Kết nối WiFi ESP32:**
   - SSID: `ESP32_Config_XXXX`
   - Password: _(không có)_

2. **Mở trình duyệt:**
   - URL: `http://192.168.4.1`
   - Giao diện cấu hình WiFi sẽ hiển thị

3. **Cấu hình:**
   - Click "🔍 Scan for Networks"
   - Chọn WiFi network của bạn
   - Nhập password
   - Click "💾 Save Configuration"

4. **Đợi kết nối:**
   - ESP32 sẽ reset và kết nối WiFi
   - Serial Monitor sẽ hiển thị IP mới

---

## 🔧 Cấu hình MQTT

MQTT đã được cấu hình trong code tại dòng 70:
```cpp
mqtt->updateConfig("192.168.1.100", 1883, CLIENT_ID);
```

**Client ID:** Đã được định nghĩa ở dòng 10
```cpp
#define CLIENT_ID "066420c45a4e819437bbfbea63b83739"
```

**MQTT Topics Subscribe:**
```cpp
mqtt->subscribe("CT/" + CLIENT_ID + "/3");  // Command topic cho Virtual Pin 3
mqtt->subscribe("SS/" + CLIENT_ID + "/5");  // Status topic cho Virtual Pin 5
```

**MQTT Topics Publish:**
- Sensor data: `SS/{CLIENT_ID}/{VirtualPin}`
- Ví dụ: `SS/066420c45a4e819437bbfbea63b83739/2`

---

## 📊 Kiểm tra hoạt động

### Test MQTT Publishing
Serial Monitor sẽ hiển thị mỗi 5 giây:
```
📤 [MQTTTask] Published: SS/066420c45a4e819437bbfbea63b83739/2 = 0
```

### Test MQTT Subscribing
Gửi command từ MQTT Broker:
```bash
mosquitto_pub -h 192.168.1.100 -t "CT/066420c45a4e819437bbfbea63b83739/3" -m "1"
```

Serial Monitor sẽ hiển thị:
```
📨 [MQTT] Received: CT/066420c45a4e819437bbfbea63b83739/3 = 1
🎛️ [GPIOManager] Processing command: 3 = 1
📤 [GPIOManager] Pin 3 set to HIGH
```

---

## 🎯 Tóm tắt nhanh

1. ✅ Cài ESP32 Board trong Arduino IDE
2. ✅ Mở file `ESP32_MultiThread_IoT.ino`
3. ✅ Chọn Board: ESP32 Dev Module
4. ✅ Chọn Port COMx
5. ✅ Sửa IP MQTT Broker
6. ✅ Click Upload (Ctrl+U)
7. ✅ Nhấn BOOT khi đang Connecting
8. ✅ Mở Serial Monitor (115200 baud)
9. ✅ Reset ESP32
10. ✅ Kiểm tra output

---

## 📞 Hỗ trợ

Nếu gặp vấn đề:
1. Kiểm tra Serial Monitor để xem thông báo lỗi
2. Kiểm tra tất cả file .h và .cpp có đầy đủ không
3. Kiểm tra ESP32 Board đã cài đặt đúng chưa
4. Kiểm tra cáp USB và driver

**Chúc bạn thành công! 🎉**

