#!/usr/bin/env python3
"""
MQTT Test Client đơn giản - Để test DIY MQTT Broker
Chỉ sử dụng socket và struct, không dùng thư viện MQTT
"""

import socket
import struct
import time
import threading

class SimpleMQTTClient:
    def __init__(self, broker_host='localhost', broker_port=1883, client_id='test_client'):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = client_id
        self.socket = None
        self.connected = False
        self.onReciveMessage = lambda topic, message: None  
    def connect(self):
        """Kết nối đến MQTT Broker"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.broker_host, self.broker_port))

            # Tạo MQTT CONNECT packet
            connect_packet = self.create_connect_packet()
            print(f"📤 Gửi CONNECT packet: {connect_packet.hex()}")

            self.socket.send(connect_packet)

            # Đợi CONNACK
            response = self.socket.recv(1024)
            print(f"📨 Nhận CONNACK: {response.hex()}")

            if len(response) >= 4 and response[0] == 0x20:  # CONNACK
                return_code = response[3]
                if return_code == 0:
                    self.connected = True
                    print("✅ Kết nối thành công!")

                    # Start receiving
                    self.receive_loop()

                    return True
                else:
                    print(f"❌ Kết nối thất bại: return code {return_code}")
                    return False

        except Exception as e:
            print(f"❌ Lỗi kết nối: {e}")
            return False

    def create_connect_packet(self):
        """Tạo MQTT CONNECT packet"""
        # MQTT CONNECT packet format:
        # Fixed header + Variable header + Payload

        # Protocol name "MQTT" (4 bytes length + "MQTT")
        protocol_name = b"\x00\x04MQTT"

        # Protocol version (3.1.1 = 4)
        protocol_version = b"\x04"

        # Connect flags (clean session = 1)
        connect_flags = b"\x02"

        # Keep alive (60 seconds)
        keep_alive = b"\x00\x3C"

        # Client ID
        client_id_bytes = self.client_id.encode('utf-8')
        client_id_length = struct.pack(">H", len(client_id_bytes))

        # Variable header + Payload
        variable_header = protocol_name + protocol_version + connect_flags + keep_alive
        payload = client_id_length + client_id_bytes

        # Calculate remaining length
        remaining_length = len(variable_header) + len(payload)

        # Fixed header
        packet_type = 0x10  # CONNECT
        fixed_header = bytes([packet_type, remaining_length])

        return fixed_header + variable_header + payload

    def subscribe(self, topic):
        """Subscribe đến một topic"""
        if not self.connected:
            print("❌ Chưa kết nối!")
            return False

        try:
            # Tạo SUBSCRIBE packet
            subscribe_packet = self.create_subscribe_packet(topic)
            print(f"📤 Gửi SUBSCRIBE '{topic}': {subscribe_packet.hex()}")

            self.socket.send(subscribe_packet)
            return True

        except Exception as e:
            print(f"❌ Lỗi subscribe: {e}")
            return False

    def create_subscribe_packet(self, topic):
        """Tạo MQTT SUBSCRIBE packet"""
        # Packet identifier (random)
        packet_id = b"\x00\x01"

        # Topic filter
        topic_bytes = topic.encode('utf-8')
        topic_length = struct.pack(">H", len(topic_bytes))
        qos = b"\x00"  # QoS 0

        # Variable header + Payload  
        variable_header = packet_id
        payload = topic_length + topic_bytes + qos

        remaining_length = len(variable_header) + len(payload)

        # Fixed header
        packet_type = 0x82  # SUBSCRIBE with QoS 1
        fixed_header = bytes([packet_type, remaining_length])

        return fixed_header + variable_header + payload

    def publish(self, topic, message):
        """Publish message đến topic"""
        if not self.connected:
            return "CHua ket noi toi broker "

        try:
            # Tạo PUBLISH packet
            publish_packet = self.create_publish_packet(topic, message)

            self.socket.send(publish_packet)
            return True

        except Exception as e:
            return f"loi khi gui {e}"

    def create_publish_packet(self, topic, message):
        """Tạo MQTT PUBLISH packet"""
        # Topic
        topic_bytes = topic.encode('utf-8')
        topic_length = struct.pack(">H", len(topic_bytes))

        # Message
        message_bytes = message.encode('utf-8')

        # Variable header + Payload
        variable_header = topic_length + topic_bytes
        payload = message_bytes

        remaining_length = len(variable_header) + len(payload)

        # Fixed header
        packet_type = 0x30  # PUBLISH
        fixed_header = bytes([packet_type, remaining_length])

        return fixed_header + variable_header + payload

    def receive_loop(self):
        """Vòng lặp nhận tin nhắn"""
        while self.connected:
            try:
                data = self.socket.recv(1024)
                if not data:
                    break

                self.handle_received_packet(data)

            except Exception as e:
                if self.connected:
                    print(f"❌ Lỗi nhận tin: {e}")
                break

    def handle_received_packet(self, data):
        """Xử lý packet nhận được"""
        if len(data) < 2:
            return

        packet_type = (data[0] >> 4) & 0x0F

        if packet_type == 3:  # PUBLISH
            self.handle_publish_packet(data)
        elif packet_type == 9:  # SUBACK
            print("✅ Nhận SUBACK - Subscribe thành công!")
        elif packet_type == 13:  # PINGRESP
            print("🏓 Nhận PINGRESP")

    def handle_publish_packet(self, data):
        """Xử lý PUBLISH packet nhận được"""
        try:
            remaining_length = data[1]
            payload = data[2:2+remaining_length]

            # Parse topic
            if len(payload) < 2:
                return

            topic_length = struct.unpack(">H", payload[0:2])[0]
            topic = payload[2:2+topic_length].decode('utf-8')
            message = payload[2+topic_length:].decode('utf-8')
            try:
                # Invoke callback if provided
                self.onReciveMessage(topic, message)
            except Exception as _cb_err:
                # Keep client robust even if user callback throws
                print(f"⚠️ onReciveMessage callback error: {_cb_err}")
            print(f"======= Nhan tin response tu sever {topic} : {message}" )
        except Exception as e:
            print(f"❌ Lỗi parse PUBLISH: {e}")

    def disconnect(self):
        """Ngắt kết nối"""
        self.connected = False
        if self.socket:
            try:
                # Gửi DISCONNECT packet
                disconnect_packet = bytes([0xE0, 0x00])
                self.socket.send(disconnect_packet)
                self.socket.close()
                print("🔌 Đã ngắt kết nối")
            except:
                pass
