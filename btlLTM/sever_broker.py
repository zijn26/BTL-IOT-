#!/usr/bin/env python3
"""
MQTT Broker đơn giản từ đầu - Không sử dụng thư viện MQTT có sẵn
Chỉ sử dụng socket, threading, struct để hiểu rõ bản chất của MQTT Broker

Tác giả: DIY MQTT Broker
Mục đích: Học tập và hiểu rõ cách hoạt động của MQTT Broker
"""

import socket
import threading
import struct
import time
from typing import Dict, List, Optional

# MQTT Control Packet Types (theo MQTT 3.1.1 specification)
MQTT_PACKET_TYPES = {
    1: 'CONNECT',
    2: 'CONNACK', 
    3: 'PUBLISH',
    4: 'PUBACK',
    5: 'PUBREC',
    6: 'PUBREL',
    7: 'PUBCOMP',
    8: 'SUBSCRIBE',
    9: 'SUBACK',
    10: 'UNSUBSCRIBE',
    11: 'UNSUBACK',
    12: 'PINGREQ',
    13: 'PINGRESP',
    14: 'DISCONNECT'
}

class SimpleMQTTBroker:
    """
    MQTT Broker đơn giản - Trái tim của IoT communication

    Đây chính là "bộ não" mà bạn muốn hiểu:
    - TCP Socket Server lắng nghe port 1883
    - Dictionary lưu subscriptions (topic -> list clients) 
    - Logic Pub/Sub: ai subscribe topic nào thì nhận tin nhắn topic đó
    """

    def __init__(self, host='localhost', port=1883):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False

        # *** CÁC CẤU TRÚC DỮ LIỆU CHÍNH - TRÁI TIM CỦA BROKER ***
        self.clients = {}                    # {client_id: socket_object}
        self.subscriptions = {}              # {topic: [list_of_client_sockets]} <- MAGIC HERE!
        self.client_subscriptions = {}       # {client_socket: [list_of_topics]}

        print(f"🔧 Khởi tạo MQTT Broker tại {host}:{port}")
        print("📊 Cấu trúc dữ liệu 'bộ não' broker:")
        print(f"   - clients: {self.clients}")
        print(f"   - subscriptions: {self.subscriptions}")
        print(f"   - client_subscriptions: {self.client_subscriptions}")

    def start(self):
        """Khởi động MQTT Broker Server"""
        try:
            # Tạo TCP Socket Server - Đây là nền tảng của mọi thứ
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            #socket.SO_REUSEADDR cho phep su dung lai port sau khi server dung
            # boi vi khi server dung, port van con duoc su dung do tcp van o che do time wait
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)  # Có thể handle 5 pending connections

            self.running = True
            print(f"\n✅ MQTT Broker đã khởi động tại {self.host}:{self.port}")
            print("🔄 Đang lắng nghe kết nối...")
            print("💡 Đây chính là socket.listen() - 'gõ cửa' từ ESP32/clients")
            print("\n" + "="*80)

            while self.running:
                try:
                    # Accept kết nối mới - Khi ESP32 gọi client.connect()
                    client_socket, address = self.socket.accept()
                    print(f"\n🌟 Kết nối mới từ: {address}")
                    print(f"🔌 Socket object: {client_socket}")

                    # Tạo thread để xử lý client này (bỏ qua threading complexity theo yêu cầu)
                    # Nhưng cần thiết để handle multiple clients
                    client_thread = threading.Thread(
                        target=self.handle_client, 
                        args=(client_socket, address),
                        daemon=True
                    )
                    client_thread.start()

                except Exception as e:
                    if self.running:
                        print(f"❌ Lỗi khi accept connection: {e}")

        except Exception as e:
            print(f"❌ Lỗi khởi động server: {e}")
        finally:
            self.stop()

    def stop(self):
        """Dừng broker"""
        self.running = False
        if self.socket:
            self.socket.close()
        print("\n🛑 MQTT Broker đã dừng")

    def handle_client(self, client_socket, address):
        """
        Xử lý một client cụ thể - Đây là vòng lặp chính của mỗi client
        Mỗi ESP32 sẽ có một thread riêng chạy function này
        """
        client_id = None
        print(f"🎯 Bắt đầu xử lý client {address}")

        try:
            while self.running:
                # Nhận dữ liệu từ client - đây là socket.recv()
                data = client_socket.recv(1024)
                if not data:
                    print(f"🔌 Client {address} đã ngắt kết nối (empty data)")
                    break

                print(f"\n📨 Nhận {len(data)} bytes từ {address}")
                print(f"🔍 Raw bytes: {data.hex()}")
                print(f"💡 Đây chính là MQTT packet được ESP32 gửi!")

                # Parse MQTT packet - Giải mã "ngôn ngữ" MQTT
                packet_type, payload = self.parse_mqtt_packet(data)
                print(f"📋 Packet đã parse: {packet_type}")

                # Xử lý các loại packet khác nhau
                if packet_type == 'CONNECT':
                    client_id = self.handle_connect(client_socket, payload, address)

                elif packet_type == 'PUBLISH':
                    print("🎯 *** ĐÂY LÀ PUBLISH - TRÁI TIM PUB/SUB! ***")
                    self.handle_publish(client_socket, payload)

                elif packet_type == 'SUBSCRIBE':
                    print("🎯 *** ĐÂY LÀ SUBSCRIBE - ĐĂNG KÝ NHẬN TIN! ***")
                    self.handle_subscribe(client_socket, payload, client_id)

                elif packet_type == 'PINGREQ':
                    self.handle_ping(client_socket)

                elif packet_type == 'DISCONNECT':
                    self.cleanup_client(client_socket, client_id)
                    break

                else:
                    print(f"⚠️ Packet type không được hỗ trợ: {packet_type}")

        except Exception as e:
            print(f"❌ Lỗi khi xử lý client {address}: {e}")
        finally:
            self.cleanup_client(client_socket, client_id)

    def parse_mqtt_packet(self, data):
        """
        Parse MQTT packet - Giải mã 'ngôn ngữ' MQTT

        MQTT packet format:
        [Fixed Header][Variable Header][Payload]

        Fixed Header:
        - Byte 1: Packet Type (bits 4-7) + Flags (bits 0-3)  
        - Byte 2+: Remaining Length
        """
        if len(data) < 2:
            return None, None

        # Byte đầu tiên chứa packet type
        first_byte = data[0]
        packet_type_num = (first_byte >> 4) & 0x0F  # Lấy 4 bits cao
        packet_type = MQTT_PACKET_TYPES.get(packet_type_num, 'UNKNOWN')
        # Byte thứ 2 là remaining length (simplified - thực tế phức tạp hơn)
        remaining_length = data[1] if len(data) > 1 else 0
        payload = data[2:2+remaining_length] if len(data) > 2 else b''
        return packet_type, payload

    def handle_connect(self, client_socket, payload, address):
        """
        Xử lý MQTT CONNECT - Client "xin chào" broker
        """
        print(f"🤝 Xử lý CONNECT từ {address}")
        print("💡 Đây như ESP32 nói: 'Tôi muốn kết nối, tôi tên là...'")

        try:
            # Parse client ID từ payload (simplified parsing)
            # Thực tế MQTT CONNECT packet phức tạp hơn nhiều
            client_id = f"client_{address[1]}"  # Đơn giản hóa

            # Nếu có payload đủ dài, thử parse client ID thật
            if len(payload) > 10:
                try:
                    # Skip protocol name và version (byte 0-9)
                    client_id_len = struct.unpack(">H", payload[8:10])[0]
                    if len(payload) >= 10 + client_id_len:
                        client_id = payload[10:10+client_id_len].decode('utf-8')
                        print(f"📝 Parsed Client ID: {client_id}")
                except:
                    pass  # Fallback to default client_id

            print(f"👤 Client ID: {client_id}")
            # *** LƯU CLIENT VÀO 'BỘ NHỚ' BROKER ***
            self.clients[client_id] = client_socket
            self.client_subscriptions[client_socket] = []

            print(f"💾 Đã lưu vào bộ nhớ broker:")
            print(f"   clients['{client_id}'] = {client_socket}")
            print(f"   client_subscriptions[socket] = []")

            # Gửi CONNACK - "Chào lại, kết nối thành công!"
            connack = bytes([0x20, 0x02, 0x00, 0x00])  # CONNACK với return code 0
            client_socket.send(connack)
            print(f"📤 Đã gửi CONNACK cho {client_id}")

            print(f"📊 TRẠNG THÁI BROKER:")
            print(f"   Clients: {list(self.clients.keys())}")
            print(f"   Subscriptions: {dict(self.subscriptions)}")

            return client_id

        except Exception as e:
            print(f"❌ Lỗi xử lý CONNECT: {e}")
            return None

    def handle_publish(self, client_socket, payload):
        """
        *** ĐÂY LÀ TRÁI TIM CỦA PUB/SUB PATTERN! ***

        Khi ESP32 gọi client.publish("nha/den", "ON"):
        1. Tìm topic "nha/den" trong subscriptions
        2. Lấy danh sách tất cả client_socket đã subscribe topic này
        3. Gửi message "ON" cho tất cả những client đó

        Đó chính là toàn bộ bí mật của MQTT!
        """
        print(f"📤 *** XỬ LÝ PUBLISH - TRÁI TIM PUB/SUB! ***")

        try:
            # Parse topic name từ MQTT PUBLISH packet
            if len(payload) < 2:
                print("❌ Payload quá ngắn")
                return

            # 2 bytes đầu là topic length
            topic_len = struct.unpack(">H", payload[0:2])[0]
            print(f"🔍 Topic length: {topic_len}")

            if len(payload) < 2 + topic_len:
                print("❌ Payload không đủ dài cho topic")
                return

            # Extract topic và message
            topic = payload[2:2+topic_len].decode('utf-8')
            message = payload[2+topic_len:].decode('utf-8')

            print(f"📝 PUBLISH RECEIVED:")
            print(f"   Topic: '{topic}'")
            print(f"   Message: '{message}'")
            print(f"💡 Giống như ESP32 gọi: client.publish('{topic}', '{message}')")

            # *** LOGIC PUB/SUB CHÍNH - ĐÂY LÀ MAGIC! ***
            print(f"\n🎯 BẮT ĐẦU LOGIC PUB/SUB:")
            print(f"🔍 Kiểm tra subscriptions['{topic}']...")

            if topic in self.subscriptions:
                subscribers = self.subscriptions[topic]
                print(f"✅ Tìm thấy {len(subscribers)} subscribers cho topic '{topic}'")
                print(f"👥 Subscribers: {subscribers}")

                # Tạo PUBLISH packet để gửi cho subscribers
                publish_packet = self.create_publish_packet(topic, message)
                print(f"📦 Tạo packet để gửi: {publish_packet.hex()}")

                # *** GỬI CHO TẤT CẢ SUBSCRIBERS - ĐÂY LÀ DISTRIBUTION! ***
                successful_sends = 0
                for subscriber_socket in subscribers:
                    try:
                        subscriber_socket.send(publish_packet)
                        successful_sends += 1
                        print(f"✅ Đã gửi message đến subscriber {subscriber_socket}")
                    except Exception as e:
                        print(f"❌ Không thể gửi đến subscriber: {e}")

                print(f"🎉 Đã gửi thành công đến {successful_sends}/{len(subscribers)} subscribers")

            else:
                print(f"📭 KHÔNG có subscriber nào cho topic '{topic}'")
                print(f"💡 Giống như không ai 'lắng nghe' topic này")

            # Hiển thị trạng thái hiện tại
            print(f"\n📊 TRẠNG THÁI SUBSCRIPTIONS:")
            for t, subs in self.subscriptions.items():
                print(f"   '{t}': {len(subs)} subscribers")

        except Exception as e:
            print(f"❌ Lỗi xử lý PUBLISH: {e}")

    def handle_subscribe(self, client_socket, payload, client_id):
        """
        *** XỬ LÝ SUBSCRIBE - ĐĂNG KÝ NHẬN TIN! ***

        Khi App điện thoại gọi client.subscribe("nha/den"):
        1. Thêm client_socket vào subscriptions["nha/den"]
        2. Từ giờ, mỗi khi có ai publish "nha/den", app sẽ nhận được

        Đó là toàn bộ logic!
        """
        print(f"📝 *** XỬ LÝ SUBSCRIBE - ĐĂNG KÝ! ***")
        print(f"👤 Client: {client_id}")

        try:
            # Parse SUBSCRIBE packet
            # Skip packet identifier (2 bytes đầu)
            offset = 2
            subscribed_topics = []

            while offset < len(payload):
                # Parse topic name
                if offset + 2 > len(payload):
                    break

                topic_len = struct.unpack(">H", payload[offset:offset+2])[0]
                offset += 2

                if offset + topic_len > len(payload):
                    break

                topic = payload[offset:offset+topic_len].decode('utf-8')
                
                offset += topic_len + 1  # +1 for QoS byte (skip)

                print(f"📌 Client {client_id} muốn subscribe: '{topic}'")
                print(f"💡 Giống như app gọi: client.subscribe('{topic}')")

                print(f"\n🎯 THỰC HIỆN SUBSCRIPTION:")

                # Tạo danh sách subscribers cho topic này nếu chưa có
                if topic not in self.subscriptions:
                    self.subscriptions[topic] = []
                    print(f"📝 Tạo mới subscriptions['{topic}'] = []")

                # Thêm client socket vào danh sách subscribers
                if client_socket not in self.subscriptions[topic]:
                    self.subscriptions[topic].append(client_socket)
                    print(f"✅ Thêm client vào subscriptions['{topic}']")
                    print(f"📊 subscriptions['{topic}'] hiện có: {len(self.subscriptions[topic])} subscribers")
                else:
                    print(f"⚠️ Client đã subscribe topic này rồi")

                # Lưu subscription cho client này (để cleanup sau)
                if topic not in self.client_subscriptions[client_socket]:
                    self.client_subscriptions[client_socket].append(topic)

                subscribed_topics.append(topic)

            # Gửi SUBACK - "Đã đăng ký thành công!"
            if subscribed_topics:
                # Simplified SUBACK packet
                suback_payload = bytes([payload[0], payload[1]]) + b'\x00' * len(subscribed_topics)
                suback = bytes([0x90, len(suback_payload)]) + suback_payload
                client_socket.send(suback)
                print(f"📤 Đã gửi SUBACK cho {client_id}")

            # Hiển thị trạng thái subscriptions
            print(f"\n📊 TRẠNG THÁI SAU KHI SUBSCRIBE:")
            print(f"👤 {client_id} đã subscribe: {self.client_subscriptions[client_socket]}")
            print(f"📊 Tất cả subscriptions:")
            for topic, subscribers in self.subscriptions.items():
                print(f"   '{topic}': {len(subscribers)} subscribers")

        except Exception as e:
            print(f"❌ Lỗi xử lý SUBSCRIBE: {e}")

    def handle_ping(self, client_socket):
        """Xử lý MQTT PINGREQ - Heartbeat"""
        print(f"🏓 Nhận PINGREQ, gửi PINGRESP")
        print(f"💡 Đây như client hỏi: 'Broker còn sống không?' và broker trả lời: 'Còn!'")
        pingresp = bytes([0xD0, 0x00])  # PINGRESP
        client_socket.send(pingresp)

    def create_publish_packet(self, topic, message):
        """
        Tạo MQTT PUBLISH packet để gửi cho subscribers

        Đây là quá trình 'đóng gói' message theo định dạng MQTT
        để gửi cho clients đã subscribe
        """
        topic_bytes = topic.encode('utf-8')
        message_bytes = message.encode('utf-8')

        # MQTT PUBLISH packet format:
        # [Fixed Header: packet type + remaining length]
        # [Variable Header: topic length + topic] 
        # [Payload: message]

        remaining_length = 2 + len(topic_bytes) + len(message_bytes)

        packet = bytearray()
        packet.append(0x30)  # PUBLISH packet type (0011 0000)
        packet.append(remaining_length)  # Remaining length (simplified)

        # Variable Header: Topic length + topic
        packet.extend(struct.pack(">H", len(topic_bytes)))  # Topic length (2 bytes big-endian)
        packet.extend(topic_bytes)

        # Payload: Message
        packet.extend(message_bytes)

        print(f"📦 Tạo PUBLISH packet:")
        print(f"   Fixed Header: [0x{packet[0]:02x}, 0x{packet[1]:02x}]")
        print(f"   Topic: '{topic}' ({len(topic_bytes)} bytes)")
        print(f"   Message: '{message}' ({len(message_bytes)} bytes)")
        print(f"   Total packet: {bytes(packet).hex()}")

        return bytes(packet)

    def cleanup_client(self, client_socket, client_id):
        """
        Dọn dẹp khi client ngắt kết nối
        Xóa client khỏi tất cả cấu trúc dữ liệu
        """
        print(f"\n🧹 DỌN DẸP CLIENT: {client_id}")
        try:
            # Xóa client khỏi clients dictionary
            if client_id and client_id in self.clients:
                del self.clients[client_id]
                print(f"✅ Xóa khỏi clients dictionary")

            # Xóa client khỏi tất cả subscriptions
            topics_to_cleanup = []
            for topic, subscribers in self.subscriptions.items():
                if client_socket in subscribers:
                    subscribers.remove(client_socket)
                    print(f"✅ Xóa client khỏi subscription '{topic}'")

                    if not subscribers:  # Nếu không còn subscriber nào
                        topics_to_cleanup.append(topic)

            # Xóa topics không còn subscribers
            for topic in topics_to_cleanup:
                del self.subscriptions[topic]
                print(f"✅ Xóa topic '{topic}' (không còn subscribers)")

            # Xóa client subscriptions
            if client_socket in self.client_subscriptions:
                del self.client_subscriptions[client_socket]

            # Đóng socket
            try:
                client_socket.close()
            except:
                pass

            print(f"📊 TRẠNG THÁI SAU CLEANUP:")
            print(f"   Clients còn lại: {list(self.clients.keys())}")
            print(f"   Topics còn lại: {list(self.subscriptions.keys())}")

        except Exception as e:
            print(f"❌ Lỗi dọn dẹp client: {e}")

# ================================
# CHƯƠNG TRÌNH CHÍNH
# ================================

# def main():
#     """Chạy MQTT Broker"""
#     print("🚀 MQTT BROKER TỪ ĐẦU - PYTHON THUẦN TÚY")
#     print("="*80)
#     print("💡 Đây là broker MQTT được viết hoàn toàn bằng Python")
#     print("🎯 Mục đích: Hiểu rõ cách hoạt động của MQTT Broker")
#     print("📚 Không sử dụng thư viện MQTT có sẵn")
#     print("\n🔧 Cấu trúc hoạt động:")
#     print("   1. TCP Socket Server lắng nghe port 1883")
#     print("   2. Parse MQTT packets từ clients")
#     print("   3. Quản lý subscriptions bằng Dictionary")
#     print("   4. Thực hiện Pub/Sub distribution")
#     print("\n📌 Để test broker:")
#     print("   - mosquitto_sub -h localhost -t 'test/topic'")
#     print("   - mosquitto_pub -h localhost -t 'test/topic' -m 'Hello'")
#     print("   - ESP32 với library PubSubClient")
#     print("\n" + "="*80)

#     broker = SimpleMQTTBroker()

#     try:
#         print("\n⏹️  Nhấn Ctrl+C để dừng broker")
#         broker.start()

#     except KeyboardInterrupt:
#         print("\n\n🛑 Đang dừng broker...")
#         broker.stop()
#         print("👋 Cảm ơn bạn đã sử dụng DIY MQTT Broker!")

# if __name__ == "__main__":
#     main()
