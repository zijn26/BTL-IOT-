# Hướng dẫn sử dụng ESP32 với MQTT và CoAP

## Tổng quan

Code ESP32 này được thiết kế để gửi dữ liệu nhiệt độ, độ ẩm lên cả MQTT Broker và CoAP Server khi chạy `TestMQTT.py`.

## Các file code

### 1. `esp32_sensor_sender.ino` - Phiên bản đầy đủ
- Cần cảm biến DHT22/DHT11 thật
- Gửi dữ liệu thực từ cảm biến
- Phù hợp cho demo thực tế

### 2. `esp32_simple_sender.ino` - Phiên bản đơn giản
- Cần cảm biến DHT22/DHT11 thật
- Code được tối ưu và dễ hiểu hơn
- Có nhiều tính năng debug

### 3. `esp32_demo_sender.ino` - Phiên bản demo
- **KHÔNG CẦN CẢM BIẾN THẬT**
- Dùng dữ liệu giả lập
- Phù hợp để test nhanh

## Cài đặt nhanh (Khuyến nghị dùng phiên bản demo)

### Bước 1: Cài đặt thư viện

Trong Arduino IDE, cài đặt:
1. **PubSubClient** - MQTT client
2. **ArduinoJson** - Xử lý JSON

### Bước 2: Cấu hình

Mở `esp32_demo_sender.ino` và thay đổi:

```cpp
// WiFi settings
const char* ssid = "TEN_WIFI_CUA_BAN";
const char* password = "MAT_KHAU_WIFI";

// Server settings - THAY ĐỔI IP CỦA MÁY CHẠY TestMQTT.py
const char* mqtt_server = "192.168.1.100";  // IP máy chạy TestMQTT.py
const char* coap_server = "192.168.1.100";  // IP máy chạy TestMQTT.py
```

### Bước 3: Upload code

1. Kết nối ESP32 với máy tính
2. Chọn Board: ESP32 Dev Module
3. Chọn Port: COM port tương ứng
4. Upload code

### Bước 4: Chạy TestMQTT.py

Trên máy tính:

```bash
cd btlLTM
python TestMQTT.py
```

Mở trình duyệt: `http://127.0.0.1:8080`

### Bước 5: Test ESP32

1. Mở Serial Monitor (115200 baud)
2. Gõ `test` để bắt đầu gửi 20 gói dữ liệu
3. Xem kết quả trên web interface

## Format dữ liệu

Dữ liệu gửi lên có format JSON:

```json
{
  "id": 1,
  "data": 25.50,
  "time": 1234567890.123,
  "humidity": 60.25,
  "sensor": "DHT22",
  "voltage": 3.28
}
```

- `id`: Số thứ tự gói (1-20)
- `data`: Nhiệt độ (°C) - đây là trường chính
- `time`: Timestamp (giây)
- `humidity`: Độ ẩm (%)
- `sensor`: Loại cảm biến
- `voltage`: Điện áp (chỉ có trong phiên bản demo)

## Các lệnh Serial Monitor

- `test` - Bắt đầu gửi 20 gói dữ liệu
- `status` - Xem trạng thái hệ thống
- `help` - Hiển thị hướng dẫn
- `reset` - Reset dữ liệu (chỉ có trong phiên bản demo)

## Troubleshooting

### Lỗi kết nối WiFi
- Kiểm tra SSID và password
- Đảm bảo WiFi 2.4GHz
- Kiểm tra khoảng cách đến router

### Lỗi kết nối MQTT/CoAP
- Kiểm tra IP server có đúng không
- Đảm bảo `TestMQTT.py` đang chạy
- Kiểm tra firewall

### ESP32 không phản hồi
- Nhấn nút RESET
- Kiểm tra kết nối USB
- Upload lại code

## So sánh các phiên bản

| Tính năng | Demo | Simple | Full |
|-----------|------|--------|------|
| Cần cảm biến | ❌ | ✅ | ✅ |
| Dữ liệu thật | ❌ | ✅ | ✅ |
| Dữ liệu giả | ✅ | ❌ | ❌ |
| Debug info | ✅ | ✅ | ✅ |
| Error handling | ✅ | ✅ | ✅ |
| CoAP support | ✅ | ✅ | ✅ |
| MQTT support | ✅ | ✅ | ✅ |

## Lưu ý quan trọng

1. **IP Server**: Phải thay đổi IP trong code cho đúng với máy chạy `TestMQTT.py`
2. **WiFi**: Chỉ hỗ trợ WiFi 2.4GHz
3. **Port**: MQTT dùng port 1883, CoAP dùng port 5683
4. **Format**: Dữ liệu phải đúng format JSON như yêu cầu
5. **Timing**: Gửi 20 gói với khoảng cách 200ms

## Mở rộng

Có thể thêm:
- Cảm biến ánh sáng
- Cảm biến áp suất
- Cảm biến chuyển động
- LED status indicators
- OLED display

## Liên hệ

Nếu có vấn đề, kiểm tra:
1. Serial Monitor output
2. Web interface tại `http://127.0.0.1:8080`
3. Log của `TestMQTT.py`