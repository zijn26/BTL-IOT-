"""
File cấu hình ví dụ cho MQTT - Sao chép và tùy chỉnh theo môi trường của bạn
"""

# ============= CẤU HÌNH 1: LOCAL BROKER (Không Authentication) =============
# Sử dụng cho development/testing local với Mosquitto hoặc EMQX
MQTT_CONFIG_LOCAL = {
    "broker": "localhost",
    "port": 1883,
    "client_id": "audio_test_client_001",
    "username": None,
    "password": None,
    "keepalive": 60,
    "qos": 1,  # 0: At most once, 1: At least once, 2: Exactly once
    "protocol": "MQTTv311",  # hoặc "MQTTv5"
    "transport": "tcp"
}

# ============= CẤU HÌNH 2: LOCAL BROKER (Có Authentication) =============
# Sử dụng khi broker yêu cầu username/password
MQTT_CONFIG_LOCAL_AUTH = {
    "broker": "localhost",
    "port": 1883,
    "client_id": "audio_test_client_001",
    "username": "mqtt_user",
    "password": "mqtt_password",
    "keepalive": 60,
    "qos": 1,
    "protocol": "MQTTv311",
    "transport": "tcp"
}

# ============= CẤU HÌNH 3: CLOUD BROKER (TLS/SSL) =============
# Sử dụng cho production với HiveMQ Cloud, AWS IoT, Azure IoT Hub, etc.
MQTT_CONFIG_CLOUD = {
    "broker": "your-broker.hivemq.cloud",  # hoặc AWS/Azure endpoint
    "port": 8883,  # Port cho TLS/SSL
    "client_id": "audio_test_client_001",
    "username": "your_username",
    "password": "your_password",
    "keepalive": 60,
    "qos": 1,
    "protocol": "MQTTv311",
    "transport": "tcp",
    "use_tls": True,
    "tls_config": {
        "ca_certs": "path/to/ca.crt",  # Certificate Authority
        "certfile": "path/to/client.crt",  # Client certificate (optional)
        "keyfile": "path/to/client.key",  # Client key (optional)
        "tls_version": "TLSv1.2"  # hoặc TLSv1.3
    }
}

# ============= CẤU HÌNH 4: WEBSOCKET TRANSPORT =============
# Sử dụng khi broker chỉ hỗ trợ WebSocket (qua HTTP/HTTPS)
MQTT_CONFIG_WEBSOCKET = {
    "broker": "broker.example.com",
    "port": 9001,  # hoặc 443 cho WSS
    "client_id": "audio_test_client_001",
    "username": "mqtt_user",
    "password": "mqtt_password",
    "keepalive": 60,
    "qos": 1,
    "protocol": "MQTTv311",
    "transport": "websockets",
    "websocket_path": "/mqtt"  # Path cho WebSocket endpoint
}

# ============= CẤU HÌNH 5: AWS IoT Core =============
# Sử dụng cho AWS IoT Core với certificate-based authentication
MQTT_CONFIG_AWS_IOT = {
    "broker": "your-endpoint.iot.region.amazonaws.com",
    "port": 8883,
    "client_id": "audio_test_client_001",
    "username": None,  # AWS IoT sử dụng certificate
    "password": None,
    "keepalive": 60,
    "qos": 1,
    "protocol": "MQTTv311",
    "transport": "tcp",
    "use_tls": True,
    "tls_config": {
        "ca_certs": "AmazonRootCA1.pem",
        "certfile": "device-certificate.pem.crt",
        "keyfile": "device-private.pem.key"
    }
}

# ============= CẤU HÌNH 6: EMQX Cloud =============
MQTT_CONFIG_EMQX = {
    "broker": "your-deployment.emqx.cloud",
    "port": 1883,  # hoặc 8883 cho TLS
    "client_id": "audio_test_client_001",
    "username": "your_username",
    "password": "your_password",
    "keepalive": 60,
    "qos": 1,
    "protocol": "MQTTv5",  # EMQX hỗ trợ MQTT 5.0
    "transport": "tcp"
}

# ============= TOPICS CONFIGURATION =============
# Định nghĩa các topics sử dụng trong hệ thống
MQTT_TOPICS = {
    # Topics cho audio streaming
    "audio_start": "device/{device_id}/audio/start",
    "audio_stop": "device/{device_id}/audio/stop",
    "audio_result": "device/{device_id}/audio/result",
    
    # Topics cho control commands
    "command": "device/{device_id}/command",
    "response": "device/{device_id}/response",
    
    # Topics cho status
    "status": "device/{device_id}/status",
    "heartbeat": "device/{device_id}/heartbeat",
    
    # Topics cho logs
    "log": "device/{device_id}/log",
    "error": "device/{device_id}/error"
}

# ============= QoS LEVELS =============
"""
QoS 0 (At most once): 
  - Message gửi 1 lần, không đảm bảo nhận được
  - Nhanh nhất, dùng cho data không quan trọng
  
QoS 1 (At least once):
  - Message đảm bảo nhận được ít nhất 1 lần
  - Có thể nhận duplicate
  - Cân bằng tốt giữa reliability và performance
  
QoS 2 (Exactly once):
  - Message đảm bảo nhận được đúng 1 lần
  - Chậm nhất, dùng cho data cực kỳ quan trọng
"""

# ============= HƯỚNG DẪN SỬ DỤNG =============
"""
1. Chọn cấu hình phù hợp với môi trường của bạn
2. Sao chép config vào test_audio_websocket.py
3. Cập nhật các thông số:
   - broker: Địa chỉ MQTT broker
   - port: Port (1883 cho TCP, 8883 cho TLS, 9001 cho WebSocket)
   - client_id: ID duy nhất cho client
   - username/password: Nếu broker yêu cầu authentication
   - topics: Cập nhật theo device_id thực tế

4. Ví dụ sử dụng trong code:

# Trong test_audio_websocket.py:
from mqtt_config_example import MQTT_CONFIG_LOCAL_AUTH, MQTT_TOPICS

MQTT_BROKER = MQTT_CONFIG_LOCAL_AUTH["broker"]
MQTT_PORT = MQTT_CONFIG_LOCAL_AUTH["port"]
MQTT_CLIENT_ID = MQTT_CONFIG_LOCAL_AUTH["client_id"]
MQTT_USERNAME = MQTT_CONFIG_LOCAL_AUTH["username"]
MQTT_PASSWORD = MQTT_CONFIG_LOCAL_AUTH["password"]
MQTT_KEEPALIVE = MQTT_CONFIG_LOCAL_AUTH["keepalive"]
MQTT_QOS = MQTT_CONFIG_LOCAL_AUTH["qos"]

# Topics
device_id = "180c89ca8d814b6d83c9fc0440505cb0"
MQTT_TOPIC_START = MQTT_TOPICS["audio_start"].format(device_id=device_id)
MQTT_TOPIC_STOP = MQTT_TOPICS["audio_stop"].format(device_id=device_id)
"""

# ============= TESTING MQTT CONNECTION =============
def test_mqtt_connection(config):
    """
    Test MQTT connection với config đã cho
    Usage: python -c "from mqtt_config_example import *; test_mqtt_connection(MQTT_CONFIG_LOCAL)"
    """
    import paho.mqtt.client as mqtt
    import time
    
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f"✅ Kết nối thành công tới {config['broker']}:{config['port']}")
            print(f"✅ Client ID: {config['client_id']}")
        else:
            print(f"❌ Kết nối thất bại với code: {rc}")
    
    client = mqtt.Client(
        client_id=config["client_id"],
        protocol=mqtt.MQTTv311 if config.get("protocol") == "MQTTv311" else mqtt.MQTTv5
    )
    
    if config.get("username") and config.get("password"):
        client.username_pw_set(config["username"], config["password"])
    
    client.on_connect = on_connect
    
    try:
        client.connect(config["broker"], config["port"], config.get("keepalive", 60))
        client.loop_start()
        time.sleep(2)
        client.loop_stop()
        client.disconnect()
    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    print("📋 MQTT Configuration Examples")
    print("=" * 60)
    print("\n1. Local Broker (No Auth):")
    print(f"   Broker: {MQTT_CONFIG_LOCAL['broker']}:{MQTT_CONFIG_LOCAL['port']}")
    print(f"   Client ID: {MQTT_CONFIG_LOCAL['client_id']}")
    
    print("\n2. Local Broker (With Auth):")
    print(f"   Broker: {MQTT_CONFIG_LOCAL_AUTH['broker']}:{MQTT_CONFIG_LOCAL_AUTH['port']}")
    print(f"   Username: {MQTT_CONFIG_LOCAL_AUTH['username']}")
    
    print("\n3. Cloud Broker (TLS/SSL):")
    print(f"   Broker: {MQTT_CONFIG_CLOUD['broker']}:{MQTT_CONFIG_CLOUD['port']}")
    print(f"   TLS: Enabled")
    
    print("\n" + "=" * 60)
    print("💡 Để test kết nối, uncomment dòng dưới:")
    print("   # test_mqtt_connection(MQTT_CONFIG_LOCAL)")

