"""
Script đơn giản để test MQTT connection
Sử dụng để verify MQTT broker đã chạy và cấu hình đúng
"""

import paho.mqtt.client as mqtt
import time
import json

# ============= CẤU HÌNH =============
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_CLIENT_ID = "test_mqtt_simple"
MQTT_USERNAME = None  # Đổi thành username nếu cần
MQTT_PASSWORD = None  # Đổi thành password nếu cần
MQTT_KEEPALIVE = 60
MQTT_QOS = 1

# Test topics
TEST_TOPIC_PUB = "test/publish"
TEST_TOPIC_SUB = "test/subscribe"

# ============= CALLBACKS =============
def on_connect(client, userdata, flags, rc):
    """Callback khi kết nối"""
    print("\n" + "=" * 60)
    if rc == 0:
        print("✅ Kết nối MQTT thành công!")
        print(f"   Broker: {MQTT_BROKER}:{MQTT_PORT}")
        print(f"   Client ID: {MQTT_CLIENT_ID}")
        print("=" * 60)
        
        # Subscribe test topic
        client.subscribe(TEST_TOPIC_SUB, qos=MQTT_QOS)
        print(f"📥 Đã subscribe topic: {TEST_TOPIC_SUB}")
    else:
        error_messages = {
            1: "Incorrect protocol version",
            2: "Invalid client identifier",
            3: "Server unavailable",
            4: "Bad username or password",
            5: "Not authorized"
        }
        error_msg = error_messages.get(rc, f"Unknown error: {rc}")
        print(f"❌ Kết nối thất bại: {error_msg}")
        print("=" * 60)

def on_disconnect(client, userdata, rc):
    """Callback khi ngắt kết nối"""
    if rc != 0:
        print(f"\n⚠️  Mất kết nối bất ngờ (code: {rc})")
    else:
        print("\n✅ Đã ngắt kết nối")

def on_publish(client, userdata, mid):
    """Callback khi publish thành công"""
    print(f"✅ Message {mid} đã được gửi thành công")

def on_subscribe(client, userdata, mid, granted_qos):
    """Callback khi subscribe thành công"""
    print(f"✅ Subscribe thành công (QoS: {granted_qos[0]})")

def on_message(client, userdata, message):
    """Callback khi nhận message"""
    print("\n" + "=" * 60)
    print("📥 NHẬN ĐƯỢC MESSAGE:")
    print(f"   Topic: {message.topic}")
    print(f"   QoS: {message.qos}")
    print(f"   Retain: {message.retain}")
    
    try:
        # Try to parse as JSON
        payload = json.loads(message.payload.decode())
        print(f"   Payload (JSON): {json.dumps(payload, indent=2)}")
    except:
        # If not JSON, show as string
        print(f"   Payload: {message.payload.decode()}")
    
    print("=" * 60)

# ============= MAIN TEST =============
def test_mqtt_connection():
    """Test MQTT connection và publish/subscribe"""
    
    print("\n" + "🧪 MQTT CONNECTION TEST" + "\n")
    print("=" * 60)
    print(f"Broker: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"Client ID: {MQTT_CLIENT_ID}")
    print(f"Username: {MQTT_USERNAME or 'None'}")
    print(f"QoS: {MQTT_QOS}")
    print("=" * 60)
    
    # Khởi tạo client
    client = mqtt.Client(
        client_id=MQTT_CLIENT_ID,
        clean_session=True,
        protocol=mqtt.MQTTv311,
        transport="tcp"
    )
    
    # Set callbacks
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_publish = on_publish
    client.on_subscribe = on_subscribe
    client.on_message = on_message
    
    # Set username/password nếu có
    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        print(f"🔐 Đã cấu hình authentication")
    
    try:
        # Kết nối
        print(f"\n🔌 Đang kết nối tới {MQTT_BROKER}:{MQTT_PORT}...")
        client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)
        
        # Bắt đầu loop
        client.loop_start()
        
        # Đợi kết nối
        time.sleep(2)
        
        if client.is_connected():
            # Test 1: Publish string message
            print("\n📤 Test 1: Gửi string message...")
            result = client.publish(
                topic=TEST_TOPIC_PUB,
                payload="Hello MQTT!",
                qos=MQTT_QOS,
                retain=False
            )
            time.sleep(1)
            
            # Test 2: Publish JSON message
            print("\n📤 Test 2: Gửi JSON message...")
            data = {
                "test": "mqtt_connection",
                "timestamp": time.time(),
                "status": "success"
            }
            result = client.publish(
                topic=TEST_TOPIC_PUB,
                payload=json.dumps(data),
                qos=MQTT_QOS,
                retain=False
            )
            time.sleep(1)
            
            # Test 3: Self-publish to subscribed topic
            print("\n📤 Test 3: Gửi message tới topic đã subscribe...")
            print(f"   (Bạn sẽ nhận được message này qua on_message callback)")
            result = client.publish(
                topic=TEST_TOPIC_SUB,
                payload="Self-test message",
                qos=MQTT_QOS,
                retain=False
            )
            time.sleep(2)
            
            print("\n" + "=" * 60)
            print("✅ TẤT CẢ TESTS ĐÃ HOÀN THÀNH")
            print("=" * 60)
            print("\n💡 Nếu bạn thấy message được nhận ở trên,")
            print("   nghĩa là MQTT hoạt động hoàn hảo!")
            print("\n💡 Bạn có thể subscribe từ terminal khác:")
            print(f"   mosquitto_sub -h {MQTT_BROKER} -t '{TEST_TOPIC_PUB}' -v")
            print(f"   mosquitto_sub -h {MQTT_BROKER} -t '{TEST_TOPIC_SUB}' -v")
            
        else:
            print("\n❌ Không thể kết nối tới MQTT broker")
            print("\n🔧 Troubleshooting:")
            print("   1. Kiểm tra MQTT broker đã chạy chưa")
            print("   2. Kiểm tra địa chỉ và port")
            print("   3. Kiểm tra firewall")
            print("   4. Kiểm tra username/password nếu có")
        
        # Đợi một chút trước khi disconnect
        print("\n⏳ Đợi 3 giây trước khi disconnect...")
        time.sleep(3)
        
    except ConnectionRefusedError:
        print("\n❌ Lỗi: Kết nối bị từ chối")
        print("   → Kiểm tra MQTT broker đã chạy chưa")
        print(f"   → Thử: mosquitto -v")
        
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        
    finally:
        # Cleanup
        print("\n🧹 Dọn dẹp...")
        client.loop_stop()
        client.disconnect()
        print("✅ Đã ngắt kết nối MQTT")
        print("\n" + "=" * 60)

if __name__ == "__main__":
    try:
        test_mqtt_connection()
    except KeyboardInterrupt:
        print("\n\n⚠️  Đã hủy bởi người dùng")
    except Exception as e:
        print(f"\n\n❌ Lỗi: {e}")

