# MQTT Service - Tích hợp MQTT Broker với FastAPI
# app/services/mqtt_service.py
import asyncio
from pickle import FALSE, TRUE
import struct
import threading
import json
import time
from typing import Dict, List, Callable, Optional
from unittest import result
from app.broker_server import TAG, TOPIC_CONTRO, TOPIC_NOFICATION, TOPIC_SENSOR , SimpleMQTTBroker
from app.database import db
from app.mqtt_client import SimpleMQTTClient
from app.security import verify_device_token
TAG = "MQTT_SERVICE"

class MQTTService:
    """
    Service để tích hợp MQTT Broker với FastAPI HTTP Server
    
    Chức năng:
    - Quản lý MQTT Broker trong FastAPI
    - Bridge giữa MQTT messages và HTTP API
    - Lưu trữ sensor data từ MQTT vào database
    - Gửi commands từ HTTP API qua MQTT
    """
    
    def __init__(self):
        self.broker = None
        self.mqtt_client = None
        self.broker_thread = None
        self.client_thread = None
        self.running = False
        self.client_running = False
        self.device_tokens = {}     # {device_token: device_info}
        self.client_is_voice = {}
    def start_client(self , host='localhost', port=1883 , token = "client-1"):
        if self.client_running : 
            print(TAG + f" client da chay roi")
            return
        self.mqtt_client = SimpleMQTTClient(host , port , token )
        self.client_running = True
        self.client_thread = threading.Thread(
            target=self._run_client,
            daemon=True
        )
        self.client_thread.start()

    def start_broker(self, host='localhost', port=1883):

        """Khởi động MQTT Broker trong thread riêng"""
        if self.running:
            print(TAG + "⚠️ MQTT Broker đã đang chạy")
            return
            
        self.broker = SimpleMQTTBroker(host, port)
        self.running = True
        
        # Chạy broker trong thread riêng để không block FastAPI
        self.broker_thread = threading.Thread(
            target=self._run_broker,
            daemon=True
        )
        self.broker_thread.start()
        
        print(f"🚀 MQTT Service đã khởi động tại {host}:{port}")
        
    def _run_client(self):
        try:
            print(TAG + f"chay client")
            self.mqtt_client.connect()
        except Exception as e:
            print(TAG + f"❌ Lỗi chạy MQTT client: {e}")
        finally:
            self.client_running = False

    def _run_broker(self):
        """Chạy MQTT Broker trong thread riêng"""
        try:
            # Override handle_publish để tích hợp với database
            original_handle_publish = self.broker.handle_publish
            self.broker.handle_publish = self._enhanced_handle_publish
            self.broker.handle_connect = self.handle_connect
            self.broker.handle_connected = self.handle_connected
            self.broker.handle_disconect = self.handle_disconect
            self.broker.start()
        except Exception as e:
            print(TAG + f"❌ Lỗi chạy MQTT Broker: {e}")
        finally:
            self.running = False
    

    def handle_connect(self, client_socket, payload, address) : 
        try:
            # Parse client ID từ payload (simplified parsing)   
            # Thực tế MQTT CONNECT packet phức tạp hơn nhiều
            print(TAG + f"ket noi tu client {client_socket} {address}")
            client_id = payload[12:12+len(payload)].decode('utf-8') # Đơn giản hóa\
            if not client_id :
                print(TAG + f"loi roi ket noi do client_id None")
                return
            device = db.execute_query(
                table="devices",
                operation="select",
                filters={"token_verify" : client_id.strip()}
            )
            
            print(TAG + f" device {device} token_verify-{repr(client_id)}")
            if not device or len(device) == 0: 
                data_device = None
            else:
                data_device = verify_device_token(device[0]["device_access_token"])

            if(data_device is None): 
                connack = bytes([0x20, 0x02, 0x00, 0x02])  # CONNACK với return code 2 tức là client id không hợp lệ 
                client_socket.send(connack)
                return None
            else:
            # *** LƯU CLIENT VÀO 'BỘ NHỚ' BROKER ***
                self.broker.clients[client_id] = client_socket
                self.broker.client_subscriptions[client_socket] = []
                self.device_tokens[client_id] = device[0]
                # Gửi CONNACK - "Chào lại, kết nối thành công!"
                connack = bytes([0x20, 0x02, 0x00, 0x00])  # CONNACK với return code 0
                client_socket.send(connack)
                self.handle_connected(client_socket , client_id)
                return client_id

        except Exception as e:
            print(TAG + f"❌ Lỗi xử lý CONNECT: {e} --- client_socket : {client_socket} ")
            return None

    def handle_connected(self ,client_socket , client_id ):
        result = db.execute_query(
            table="devices",
            operation="update",
            data={"connection_status": "ONLINE"},
            filters={"token_verify": client_id}
        )
        if not result :
            print(TAG + f'Khong the chuyen thiet bi sang ON')

    def handle_disconect(self , client_socket, client_id):
        """
            -khong chac hoat dong
            -mac du da dung _handle_device_status 
        """
        result = db.execute_query(
            table="devices",
            operation="update",
            data={"connection_status": "OFFLINE"},
            filters={"token_verify": client_id}
        )
        if not result :
            print(TAG + f'Khong the chuyen thiet bi sang OFF')

    def _enhanced_handle_publish(self, client_socket, payload):
        """
        Enhanced publish handler - Tích hợp với database
        
        Khi nhận MQTT message:
        1. Parse topic và message
        2. Lưu vào database nếu là sensor data
        3. Gọi message handlers
        4. Forward cho subscribers
        """
        try:
            # Parse MQTT packet
            if len(payload) < 2:
                return
                
            topic_len = struct.unpack(">H", payload[0:2])[0]
            if len(payload) < 2 + topic_len:
                return
                
            topic = payload[2:2+topic_len].decode('utf-8')
            message = payload[2+topic_len:].decode('utf-8')
            
            print(f"📨 MQTT Message: {topic} -> {message}")
            
            # Xử lý sensor data
            if topic.startswith(TOPIC_SENSOR):
                self._handle_sensor_data(topic, message)
            if topic.startswith(TOPIC_NOFICATION):
                self._handle_notification(topic, message)
            # Xử lý device status
            # elif topic.startswith("device/"):
            #     self._handle_device_status(topic, message)
                
            # Gọi custom handlers
            # self._call_message_handlers(topic, message)
            
            # Forward cho subscribers (original logic)
            if topic in self.broker.subscriptions:
                subscribers = self.broker.subscriptions[topic]
                publish_packet = self.broker.create_publish_packet(topic, message)
                
                for subscriber_socket in subscribers:
                    try:
                        if subscriber_socket == client_socket:
                            continue
                        print(TAG + f"🔔 Phan hoi message đến subscriber: {subscriber_socket}")
                        subscriber_socket.send(publish_packet)
                    except Exception as e:
                        print(TAG + f"❌ Không thể gửi đến subscriber: {e}")
                        
        except Exception as e:
            print(f"❌ Lỗi xử lý MQTT message: {e}")
            
    def _handle_sensor_data(self, topic: str, message: str):
        
        """Xử lý sensor data từ MQTT"""
        try:
            # Parse topic: SS/{device_token}/{virtual_pin}
            parts = topic.split('/')
            if len(parts) >= 3:
                token_verify = parts[1]
                virtual_pin = int(parts[2])
                device_token = self.device_tokens[token_verify]["device_token"]
                result = db.execute_query(
                    table="device_pins",
                    operation="select",
                    filters={"device_token": device_token, "virtual_pin": virtual_pin}
                )
                if not result:
                    print(TAG + f" Khoong tim thay device_pin {device_token} {virtual_pin}")
                    self.publish_message_fromHOST(topic, "ERROR_DEVICE_PIN_NOT_FOUND")
                    return False
                elif not result[0]["pin_type"] == "INPUT":
                    print(TAG + f" Device pin {token_verify} - {virtual_pin} khong phai la INPUT")
                    self.publish_message_fromHOST(topic, "ERROR_DEVICE_PIN_NOT_TYPE_INPUT")
                    return False

                # Lưu vào database
                sensor_data = {
                    "token_verify": token_verify,
                    "virtual_pin": virtual_pin,
                    "value_string": "0" if message == "nan" else message,
                    "value_numeric": float(message) if message.replace('.', '', 1).isdigit() else 0
                }
                
                result = db.execute_query(
                    table="sensor_data",
                    operation="insert",
                    data=sensor_data
                )
                
                if result:
                    print(f"✅ Đã lưu sensor data: {sensor_data} --- clients {token_verify}" )
                else:
                    print(f"❌ Không thể lưu sensor data -- client {token_verify}")
                    
        except Exception as e:
            print(f"❌ Lỗi xử lý sensor data: {e}")
            
    def _handle_notification(self, topic: str, message: str):
        """Xử lý notification từ MQTT"""
        try:
            # Parse topic: NC/{client_id}
            #message : ER: loi 
            #   AU:ON | AU:OFF
            parts = topic.split('/')
            print(TAG + f"🔔 Notification: {parts[1]} - {message}")
            if len(parts) >= 2:
                client_id = parts[1]
            if(message.startswith("ER")):
                # self.client_is_voice[client_id] = "ERROR"
                print(TAG + f"loi roi ")
            elif(message.startswith("AU")):
                self.client_is_voice[client_id] = message.split(":")[1] == "ON"
                
        except Exception as e:
            print(f"❌ Lỗi xử lý notification: {e}")
    # xxxxxxxxxxxxxxxxxxxxxxx
    def _handle_device_status(self, topic: str, message: str):
        """Xử lý device status từ MQTT"""
        try:
            # Parse topic: device/{device_token}/status
            parts = topic.split('/')
            if len(parts) >= 3:
                device_token = parts[1]
                status = message
                
                # Cập nhật device status trong database
                result = db.execute_query(
                    table="devices",
                    operation="update",
                    data={"is_online": status == "online"},
                    filters={"device_token": device_token}
                )
                
                if result:
                    print(f"✅ Đã cập nhật device status: {device_token} -> {status}")
                    
        except Exception as e:
            print(f"❌ Lỗi xử lý device status: {e}")
    
            
    def _call_message_handlers(self, topic: str, message: str):
        """Gọi các message handlers đã đăng ký"""
        if topic in self.message_handlers:
            for handler in self.message_handlers[topic]:
                try:
                    handler(topic, message)
                except Exception as e:
                    print(f"❌ Lỗi trong message handler: {e}")
                    
    def add_message_handler(self, topic: str, handler: Callable):
        """Đăng ký handler cho topic cụ thể"""
        if topic not in self.message_handlers:
            self.message_handlers[topic] = []
        self.message_handlers[topic].append(handler)
        print(f"📝 Đã đăng ký handler cho topic: {topic}")


    def publish_message_CT(self , client_id , virtualPin ,  message):
        if not client_id :
            print(TAG + f" Client id khong ton tai")
            return False
        try :
            # Tạo MQTT PUBLISH packet0-
            #CT/{device_token}/virtualpin 
            topic = TOPIC_CONTRO + client_id +"/"+str(virtualPin)
            publish_packet = self.broker.create_publish_packet(topic, message)
            self.broker.clients.get(client_id).send(publish_packet)
            print(TAG + f"📤 Đã publish: {topic} -> {message}")
            return True
            
        except Exception as e:
            print(TAG + f"❌ Lỗi khi gửi messsage CT {client_id}" + str(e))
            return False

    def publish_message_fromHOST(self, topic: str, message: str):
        """Publish message qua MQTT (từ HTTP API)"""
        if not self.broker or not self.running:
            print("❌ MQTT Broker chưa khởi động")
            return False
            
        try:
            # Tạo MQTT PUBLISH packet
            publish_packet = self.broker.create_publish_packet(topic, message)
            
            # Gửi cho tất cả subscribers
            if topic in self.broker.subscriptions:
                subscribers = self.broker.subscriptions[topic]
                for subscriber_socket in subscribers:
                    try:
                        subscriber_socket.send(publish_packet)
                    except Exception as e:
                        print(f"❌ Không thể gửi message: {e}")
                        
            print(TAG + f"📤 Đã publish: {topic} -> {message}")
            return True
            
        except Exception as e:
            print(TAG + f"❌ Lỗi publish message: {e}")
            return False
            
    def get_subscribers_count(self, topic: str) -> int:
        """Lấy số lượng subscribers cho topic"""
        if self.broker and topic in self.broker.subscriptions:
            return len(self.broker.subscriptions[topic])
        return 0
        
    def get_all_topics(self) -> List[str]:
        """Lấy danh sách tất cả topics"""
        if self.broker:
            return list(self.broker.subscriptions.keys())
        return []
        
    def stop_broker(self):
        """Dừng MQTT Broker"""
        if self.broker:
            self.broker.stop()
        self.running = False
        print("🛑 MQTT Service đã dừng")

    def stop_client(self):
        """Dừng MQTT client"""
        if self.mqtt_client:
            self.mqtt_client.disconnect()
        self.client_running = False
        print("🛑--- MQTT Client đã dừng")

# Global MQTT Service instance
mqtt_service = MQTTService()
