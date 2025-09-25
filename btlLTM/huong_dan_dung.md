# DIY MQTT Broker - Python thuần túy

Đây là MQTT Broker được viết hoàn toàn bằng Python thuần túy, không sử dụng thư viện MQTT có sẵn.
Mục đích: Hiểu rõ cách hoạt động của MQTT Broker từ socket TCP đến Pub/Sub pattern.

## Files

- `simple_mqtt_broker.py`: MQTT Broker chính
- `mqtt_test_client.py`: Client test đơn giản  
- `README.md`: Hướng dẫn này

## Cách chạy

### 1. Chạy Broker
```bash
python simple_mqtt_broker.py
```

### 2. Test bằng client tự tạo
```bash
python mqtt_test_client.py
```

### 3. Test bằng mosquitto clients
```bash
# Terminal 1 - Subscribe
mosquitto_sub -h localhost -t "test/topic"

# Terminal 2 - Publish  
mosquitto_pub -h localhost -t "test/topic" -m "Hello World"
```

### 4. Test bằng ESP32
```cpp
#include <WiFi.h>
#include <PubSubClient.h>

WiFiClient espClient;
PubSubClient client(espClient);

void setup() {
  // Kết nối WiFi...

  client.setServer("your_broker_ip", 1883);
  client.setCallback(callback);
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.println("Message received!");
}
```

## Cấu trúc hoạt động

### TCP Socket Server
```python
self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
self.socket.bind(('localhost', 1883))
self.socket.listen(5)
```

### Cấu trúc dữ liệu chính
```python
self.subscriptions = {
    'nha/den': [socket1, socket2],
    'cam_bien/nhiet_do': [socket3, socket4]
}
```

### Logic Pub/Sub
1. **SUBSCRIBE**: Thêm client socket vào `subscriptions[topic]`
2. **PUBLISH**: Tìm tất cả socket trong `subscriptions[topic]` và gửi tin
3. Đó là tất cả!

## Tính năng được implement

✅ TCP Socket Server
✅ MQTT Protocol parsing (cơ bản)
✅ CONNECT/CONNACK
✅ PUBLISH (QoS 0)
✅ SUBSCRIBE/SUBACK
✅ PINGREQ/PINGRESP
✅ DISCONNECT
✅ Multi-client support
✅ Topic-based routing
✅ Automatic cleanup

## Tính năng chưa implement (để đơn giản)

❌ Authentication/Authorization
❌ SSL/TLS
❌ QoS 1,2 
❌ Retained messages
❌ Will messages
❌ Message persistence
❌ Wildcard topics (+, #)
❌ $SYS topics

## Logs mẫu

```
🚀 MQTT Broker đã khởi động tại localhost:1883
🌟 Kết nối mới từ: ('127.0.0.1', 54321)
🤝 Xử lý CONNECT từ ('127.0.0.1', 54321)
👤 Client ID: test_client
✅ Đã gửi CONNACK cho test_client
📝 *** XỬ LÝ SUBSCRIBE - ĐĂNG KÝ! ***
📌 Client test_client muốn subscribe: 'test/topic'
✅ Thêm client vào subscriptions['test/topic']
📤 *** XỬ LÝ PUBLISH - TRÁI TIM PUB/SUB! ***
📝 PUBLISH RECEIVED:
   Topic: 'test/topic'
   Message: 'Hello World'
✅ Tìm thấy 1 subscribers cho topic 'test/topic'
✅ Đã gửi message đến subscriber
```

## Ý nghĩa giáo dục

Broker này giúp bạn hiểu:
- MQTT chỉ là TCP socket với protocol parsing
- Pub/Sub pattern chỉ là Dictionary mapping
- "Bộ não" broker là cấu trúc dữ liệu đơn giản
- MQTT không có gì "magical", chỉ là software engineering

Enjoy coding! 🚀
