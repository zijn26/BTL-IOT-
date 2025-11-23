"""
Script để test WebSocket Audio Streaming API
- Gửi MQTT message để bắt đầu ghi âm
- Kết nối WebSocket và gửi audio chunks
- Gửi MQTT message để dừng ghi âm
- Nhận text kết quả từ WebSocket
"""

import asyncio
import pyaudio
import websockets
import paho.mqtt.client as mqtt
import time
import json
from datetime import datetime

# ============= CẤU HÌNH =============
# WebSocket Configuration
WEBSOCKET_URL = "ws://localhost:8000/audio_stream/ws/180c89ca8d814b6d83c9fc0440505cb0"
CLIENT_ID = "180c89ca8d814b6d83c9fc0440505cb0"

# MQTT Configuration
MQTT_BROKER = "localhost"  # Địa chỉ MQTT broker
MQTT_PORT = 1883
MQTT_CLIENT_ID = "638918841ae79f59b04175518bef9a73"  # Client ID cho MQTT
MQTT_USERNAME = None  # Username (None nếu không cần auth)
MQTT_PASSWORD = None  # Password (None nếu không cần auth)
MQTT_KEEPALIVE = 60  # Keepalive interval (seconds)
MQTT_QOS = 1  # Quality of Service (0, 1, hoặc 2)
MQTT_TOPIC_START = "NC/180c89ca8d814b6d83c9fc0440505cb0"  # Topic để báo bắt đầu ghi âm
MQTT_TOPIC_STOP = "NC/180c89ca8d814b6d83c9fc0440505cb0"   # Topic để báo dừng ghi âm

# Audio Configuration
CHUNK_DURATION_MS = 32  # Thời gian mỗi chunk (milliseconds)
FORMAT = pyaudio.paInt16  # Format audio 16-bit
CHANNELS = 1  # Mono audio
RATE = 16000  # Sample rate 16kHz (phù hợp cho STT)
RECORD_SECONDS = 5  # Thời gian ghi âm (có thể thay đổi)

# Tính toán chunk size
# 32ms với 16kHz = 16000 * 0.032 = 512 samples
CHUNK_SAMPLES = int(RATE * CHUNK_DURATION_MS / 1000)  # 512 samples
BYTES_PER_SAMPLE = 2  # 16-bit = 2 bytes
CHUNK_BYTES = CHUNK_SAMPLES * BYTES_PER_SAMPLE  # 512 * 2 = 1024 bytes

# ============= MQTT CLIENT =============
mqtt_client = None
mqtt_connected = False

def on_mqtt_connect(client, userdata, flags, rc):
    """Callback khi kết nối MQTT thành công/thất bại"""
    global mqtt_connected
    if rc == 0:
        print(f"✅ [MQTT] Đã kết nối tới broker: {MQTT_BROKER}:{MQTT_PORT}")
        print(f"✅ [MQTT] Client ID: {MQTT_CLIENT_ID}")
        mqtt_connected = True
    else:
        error_messages = {
            1: "Incorrect protocol version",
            2: "Invalid client identifier",
            3: "Server unavailable",
            4: "Bad username or password",
            5: "Not authorized"
        }
        error_msg = error_messages.get(rc, f"Unknown error code: {rc}")
        print(f"❌ [MQTT] Kết nối thất bại - {error_msg}")

def on_mqtt_disconnect(client, userdata, rc):
    """Callback khi ngắt kết nối MQTT"""
    global mqtt_connected
    mqtt_connected = False
    if rc != 0:
        print(f"⚠️  [MQTT] Mất kết nối bất ngờ (code: {rc})")

def on_mqtt_publish(client, userdata, mid):
    """Callback khi publish message thành công"""
    print(f"📤 [MQTT] Message đã được gửi thành công (ID: {mid})")

def init_mqtt_client():
    """Khởi tạo và cấu hình MQTT client"""
    global mqtt_client
    
    # Tạo client với Protocol v3.1.1 (MQTTv311) hoặc v5 (MQTTv5)
    mqtt_client = mqtt.Client(
        client_id=MQTT_CLIENT_ID,
    #   clean_session=True,
    #     userdata=None,  
    #     protocol=mqtt.MQTTv311,  # Có thể đổi thành mqtt.MQTTv5 nếu broker hỗ trợ
        transport="tcp"
    )
    
    # Set username và password nếu có
    # if MQTT_USERNAME and MQTT_PASSWORD:
    #     mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        # print(f"🔐 [MQTT] Đã cấu hình authentication: {MQTT_USERNAME}")
    
    # Set callbacks
    mqtt_client.on_connect = on_mqtt_connect
    mqtt_client.on_disconnect = on_mqtt_disconnect
    mqtt_client.on_publish = on_mqtt_publish
    
    # Optional: Set TLS/SSL nếu cần
    # mqtt_client.tls_set(ca_certs="path/to/ca.crt")
    
    return mqtt_client

def send_mqtt_message(topic, payload):
    """Gửi message tới MQTT broker với QoS"""
    if mqtt_connected:
        # Nếu payload là string, gửi trực tiếp; nếu là dict/object thì JSON serialize
        if isinstance(payload, str):
            message_payload = payload
        else:
            message_payload = json.dumps(payload)
        
        result = mqtt_client.publish(
            topic=topic,
            payload=message_payload,
            # qos=MQTT_QOS,
            # retain=False
        )
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"📡 [MQTT] Đã gửi message tới topic '{topic}': {payload}")
            return True
        else:
            print(f"❌ [MQTT] Gửi message thất bại với code: {result.rc}")
            return False
    else:
        print("⚠️  [MQTT] Chưa kết nối tới broker")
        return False

# ============= AUDIO RECORDING =============
async def record_and_stream_audio(websocket, duration_seconds):
    """
    Ghi âm và gửi audio qua WebSocket
    """
    audio = pyaudio.PyAudio()
    
    try:
        # Mở stream audio
        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK_SAMPLES  # 512 samples
        )
        
        print(f"🎤 [AUDIO] Bắt đầu ghi âm trong {duration_seconds} giây...")
        print(f"🎤 [AUDIO] Format: {CHANNELS} channel(s), {RATE}Hz")
        print(f"🎤 [AUDIO] Chunk: {CHUNK_SAMPLES} samples ({CHUNK_DURATION_MS}ms) = {CHUNK_BYTES} bytes")
        
        start_time = time.time()
        chunks_sent = 0
        
        while (time.time() - start_time) < duration_seconds:
            # Đọc audio chunk từ microphone (512 samples = 32ms)
            audio_data = stream.read(CHUNK_SAMPLES, exception_on_overflow=False)
            
            # Gửi qua WebSocket
            await websocket.send(audio_data)
            chunks_sent += 1
            
            # Hiển thị progress
            elapsed = time.time() - start_time
            remaining = duration_seconds - elapsed
            print(f"⏱️  [{elapsed:.1f}s/{duration_seconds}s] Đã gửi {chunks_sent} chunks | Còn lại: {remaining:.1f}s", end='\r')
        
        print(f"\n✅ [AUDIO] Đã gửi tổng cộng {chunks_sent} audio chunks")
        
        # Đóng stream
        stream.stop_stream()
        stream.close()
        
    except Exception as e:
        print(f"\n❌ [AUDIO] Lỗi khi ghi âm: {e}")
    finally:
        audio.terminate()

# ============= WEBSOCKET CLIENT =============
async def test_audio_websocket():
    """
    Test WebSocket với audio streaming
    """
    websocket_url = WEBSOCKET_URL
    
    print("=" * 60)
    print("🚀 BẮT ĐẦU TEST AUDIO WEBSOCKET")
    print("=" * 60)
    print(f"Client ID: {CLIENT_ID}")
    print(f"WebSocket URL: {websocket_url}")
    print(f"Thời gian ghi âm: {RECORD_SECONDS} giây")
    print("=" * 60)
    
    # Bước 1: Khởi tạo và kết nối MQTT
    print("\n📡 [Bước 1] Khởi tạo và kết nối tới MQTT Broker...")
    try:
        # Khởi tạo MQTT client
        init_mqtt_client()
        
        # Kết nối tới broker
        print(f"🔌 [MQTT] Đang kết nối tới {MQTT_BROKER}:{MQTT_PORT}...")
        mqtt_client.connect(
            host=MQTT_BROKER,
            port=MQTT_PORT,
            keepalive=MQTT_KEEPALIVE
        )
        
        # Bắt đầu loop để xử lý network traffic
        mqtt_client.loop_start()
        
        # Đợi kết nối MQTT
        timeout = 5
        start = time.time()
        while not mqtt_connected and (time.time() - start) < timeout:
            await asyncio.sleep(0.1)
        
        if not mqtt_connected:
            print("❌ Không thể kết nối tới MQTT broker trong 5 giây")
            return
            
    except Exception as e:
        print(f"❌ [MQTT] Lỗi kết nối: {e}")
        return
    
    # Bước 2: Gửi MQTT message để bắt đầu ghi âm
    print("\n📤 [Bước 2] Gửi gói tin MQTT để báo BẮT ĐẦU ghi âm...")

    send_mqtt_message(MQTT_TOPIC_START, "AU:ON")
    await asyncio.sleep(0.5)  # Đợi server xử lý
    
    # Bước 3: Kết nối WebSocket
    print("\n🔌 [Bước 3] Kết nối WebSocket...")
    try:
        async with websockets.connect(websocket_url) as websocket:
            print(f"✅ [WebSocket] Đã kết nối tới: {websocket_url}")
            
            # Bước 4: Ghi âm và gửi audio
            print(f"\n🎤 [Bước 4] Ghi âm và gửi audio qua WebSocket...")
            await record_and_stream_audio(websocket, RECORD_SECONDS)
            
            # Bước 5: Gửi MQTT message để dừng
            print(f"\n📤 [Bước 5] Gửi gói tin MQTT để báo DỪNG ghi âm...")
            send_mqtt_message(MQTT_TOPIC_STOP, "AU:OFF")
            await asyncio.sleep(0.5)  # Đợi server xử lý
            
            # Bước 6: Nhận text kết quả từ WebSocket
            print(f"\n📥 [Bước 6] Chờ nhận text kết quả từ WebSocket...")
            try:
                # Đợi nhận message với timeout
                result_text = await asyncio.wait_for(websocket.recv(), timeout=10)
                print(f"✅ [WebSocket] Nhận được kết quả:")
                print("=" * 60)
                print(f"📝 TEXT: {result_text}")
                print("=" * 60)
            except asyncio.TimeoutError:
                print("⚠️  [WebSocket] Timeout - Không nhận được kết quả trong 10 giây")
            except Exception as e:
                print(f"❌ [WebSocket] Lỗi khi nhận message: {e}")
            
    except websockets.exceptions.WebSocketException as e:
        print(f"❌ [WebSocket] Lỗi kết nối: {e}")
    except Exception as e:
        print(f"❌ [WebSocket] Lỗi không xác định: {e}")
    finally:
        # Cleanup
        print("\n🧹 Dọn dẹp và đóng kết nối...")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        print("✅ Hoàn tất!")

# ============= MAIN =============
if __name__ == "__main__":
    try:
        asyncio.run(test_audio_websocket())
    except KeyboardInterrupt:
        print("\n⚠️  Đã hủy bởi người dùng")
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")

