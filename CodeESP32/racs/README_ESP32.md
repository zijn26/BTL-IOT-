# ESP32 Sensor Data Sender

Code Arduino cho ESP32 để gửi dữ liệu nhiệt độ, độ ẩm lên MQTT Broker và CoAP Server.

## Yêu cầu phần cứng

- ESP32 Development Board
- DHT22 hoặc DHT11 sensor
- Dây nối (jumper wires)
- Breadboard (tùy chọn)

## Kết nối phần cứng

```
DHT22/11    ESP32
VCC    ->   3.3V
GND    ->   GND  
DATA   ->   GPIO4
```

## Yêu cầu thư viện

Cài đặt các thư viện sau trong Arduino IDE:

1. **WiFi** (có sẵn)
2. **PubSubClient** - MQTT client
   - Tools -> Manage Libraries -> Tìm "PubSubClient" -> Install
3. **ArduinoJson** - Xử lý JSON
   - Tools -> Manage Libraries -> Tìm "ArduinoJson" -> Install
4. **DHT sensor library** - Đọc cảm biến DHT
   - Tools -> Manage Libraries -> Tìm "DHT sensor library" -> Install

## Cấu hình

### 1. Cấu hình WiFi

Mở file `.ino` và thay đổi:

```cpp
const char* ssid = "YOUR_WIFI_SSID";        // Tên WiFi của bạn
const char* password = "YOUR_WIFI_PASSWORD"; // Mật khẩu WiFi
```

### 2. Cấu hình IP Server

Thay đổi IP của máy chạy `TestMQTT.py`:

```cpp
const char* mqtt_server = "192.168.1.100";  // IP máy chạy TestMQTT.py
const char* coap_server = "192.168.1.100";  // IP máy chạy TestMQTT.py
```

**Cách tìm IP:**
- Windows: `ipconfig` trong Command Prompt
- Linux/Mac: `ifconfig` trong Terminal
- Hoặc xem trong router admin panel

### 3. Cấu hình cảm biến

Nếu dùng DHT11 thay vì DHT22:

```cpp
#define DHT_TYPE DHT11  // Thay đổi từ DHT22
```

## Cách sử dụng

### 1. Upload code lên ESP32

1. Kết nối ESP32 với máy tính qua USB
2. Chọn Board: ESP32 Dev Module
3. Chọn Port: COM port tương ứng
4. Upload code

### 2. Mở Serial Monitor

- Baud rate: 115200
- Gõ `test` để bắt đầu gửi 20 gói dữ liệu
- Gõ `status` để xem trạng thái
- Gõ `help` để xem hướng dẫn

### 3. Chạy TestMQTT.py

Trên máy tính chạy:

```bash
cd btlLTM
python TestMQTT.py
```

Mở trình duyệt: `http://127.0.0.1:8080`

## Format dữ liệu

Dữ liệu gửi lên có format JSON:

```json
{
  "id": 1,
  "data": 25.50,
  "time": 1234567890.123,
  "humidity": 60.25,
  "sensor": "DHT22"
}
```

- `id`: Số thứ tự gói (1-20)
- `data`: Nhiệt độ (°C)
- `time`: Timestamp (giây)
- `humidity`: Độ ẩm (%)
- `sensor`: Loại cảm biến

## Troubleshooting

### Lỗi kết nối WiFi

- Kiểm tra SSID và password
- Đảm bảo WiFi 2.4GHz (ESP32 không hỗ trợ 5GHz)
- Kiểm tra khoảng cách đến router

### Lỗi kết nối MQTT/CoAP

- Kiểm tra IP server có đúng không
- Đảm bảo `TestMQTT.py` đang chạy
- Kiểm tra firewall có chặn port 1883, 5683 không

### Lỗi đọc cảm biến

- Kiểm tra kết nối dây
- Thử thay đổi GPIO pin
- Kiểm tra nguồn 3.3V

### ESP32 không phản hồi

- Nhấn nút RESET trên ESP32
- Kiểm tra kết nối USB
- Thử upload lại code

## Các lệnh Serial Monitor

- `test` - Bắt đầu gửi 20 gói dữ liệu
- `status` - Xem trạng thái hệ thống  
- `help` - Hiển thị hướng dẫn

## Lưu ý

- ESP32 sẽ gửi 20 gói dữ liệu với khoảng cách 200ms
- Sau khi gửi xong, cần gõ `test` lại để gửi tiếp
- Dữ liệu được gửi đồng thời lên cả MQTT và CoAP server
- Có thể xem dữ liệu real-time trên web interface

## Mở rộng

Có thể thêm các cảm biến khác:

```cpp
// Thêm cảm biến ánh sáng
#define LIGHT_PIN A0

// Đọc giá trị ánh sáng
int lightValue = analogRead(LIGHT_PIN);
doc["light"] = lightValue;
```

Hoặc thay đổi topic MQTT:

```cpp
const char* mqtt_topic = "sensors/temperature";
```