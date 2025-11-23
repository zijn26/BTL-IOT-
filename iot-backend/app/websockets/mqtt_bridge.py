# WebSocket Bridge giữa MQTT và HTTP
# app/websockets/mqtt_bridge.py
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import asyncio
from app.services.mqtt_service import mqtt_service

class MQTTWebSocketBridge:
    """
    WebSocket Bridge để kết nối MQTT với WebSocket clients
    
    Chức năng:
    - Kết nối WebSocket clients với MQTT topics
    - Forward MQTT messages đến WebSocket clients
    - Cho phép WebSocket clients subscribe MQTT topics
    """
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.topic_subscriptions: Dict[str, List[str]] = {}  # {topic: [connection_ids]}
        self.connection_topics: Dict[str, List[str]] = {}     # {connection_id: [topics]}
        
    async def connect(self, websocket: WebSocket, connection_id: str):
        """Kết nối WebSocket client"""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        self.connection_topics[connection_id] = []
        print(f"🔌 WebSocket client connected: {connection_id}")
        
    def disconnect(self, connection_id: str):
        """Ngắt kết nối WebSocket client"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            
        # Xóa subscriptions
        if connection_id in self.connection_topics:
            topics = self.connection_topics[connection_id]
            for topic in topics:
                if topic in self.topic_subscriptions:
                    if connection_id in self.topic_subscriptions[topic]:
                        self.topic_subscriptions[topic].remove(connection_id)
                    if not self.topic_subscriptions[topic]:
                        del self.topic_subscriptions[topic]
            del self.connection_topics[connection_id]
            
        print(f"🔌 WebSocket client disconnected: {connection_id}")
        
    async def subscribe_topic(self, connection_id: str, topic: str):
        """Subscribe WebSocket client vào MQTT topic"""
        if connection_id not in self.active_connections:
            return False
            
        # Thêm vào topic subscriptions
        if topic not in self.topic_subscriptions:
            self.topic_subscriptions[topic] = []
        if connection_id not in self.topic_subscriptions[topic]:
            self.topic_subscriptions[topic].append(connection_id)
            
        # Thêm vào connection topics
        if connection_id not in self.connection_topics:
            self.connection_topics[connection_id] = []
        if topic not in self.connection_topics[connection_id]:
            self.connection_topics[connection_id].append(topic)
            
        # Đăng ký MQTT handler cho topic này
        mqtt_service.add_message_handler(topic, self._handle_mqtt_message)
        
        print(f"📝 WebSocket {connection_id} subscribed to topic: {topic}")
        return True
        
    async def unsubscribe_topic(self, connection_id: str, topic: str):
        """Unsubscribe WebSocket client khỏi MQTT topic"""
        if connection_id in self.topic_subscriptions.get(topic, []):
            self.topic_subscriptions[topic].remove(connection_id)
            if not self.topic_subscriptions[topic]:
                del self.topic_subscriptions[topic]
                
        if connection_id in self.connection_topics and topic in self.connection_topics[connection_id]:
            self.connection_topics[connection_id].remove(topic)
            
        print(f"📝 WebSocket {connection_id} unsubscribed from topic: {topic}")
        return True
        
    def _handle_mqtt_message(self, topic: str, message: str):
        """Handle MQTT message và forward đến WebSocket clients"""
        if topic in self.topic_subscriptions:
            connection_ids = self.topic_subscriptions[topic]
            
            # Tạo message data
            message_data = {
                "type": "mqtt_message",
                "topic": topic,
                "message": message,
                "timestamp": str(asyncio.get_event_loop().time())
            }
            
            # Forward đến tất cả subscribed connections
            for connection_id in connection_ids:
                if connection_id in self.active_connections:
                    asyncio.create_task(
                        self._send_to_websocket(connection_id, message_data)
                    )
                    
    async def _send_to_websocket(self, connection_id: str, data: dict):
        """Gửi data đến WebSocket client"""
        try:
            websocket = self.active_connections[connection_id]
            await websocket.send_text(json.dumps(data))
        except Exception as e:
            print(f"❌ Lỗi gửi data đến WebSocket {connection_id}: {e}")
            # Xóa connection nếu lỗi
            self.disconnect(connection_id)
            
    async def send_to_connection(self, connection_id: str, data: dict):
        """Gửi data đến specific WebSocket connection"""
        if connection_id in self.active_connections:
            await self._send_to_websocket(connection_id, data)
            return True
        return False
        
    async def broadcast_to_topic(self, topic: str, data: dict):
        """Broadcast data đến tất cả clients subscribed topic"""
        if topic in self.topic_subscriptions:
            connection_ids = self.topic_subscriptions[topic]
            for connection_id in connection_ids:
                await self._send_to_websocket(connection_id, data)
                
    def get_connection_info(self, connection_id: str) -> dict:
        """Lấy thông tin connection"""
        if connection_id in self.active_connections:
            return {
                "connection_id": connection_id,
                "topics": self.connection_topics.get(connection_id, []),
                "connected": True
            }
        return {"connection_id": connection_id, "connected": False}
        
    def get_all_connections(self) -> List[dict]:
        """Lấy thông tin tất cả connections"""
        connections = []
        for connection_id in self.active_connections:
            connections.append(self.get_connection_info(connection_id))
        return connections
        
    def get_topic_info(self, topic: str) -> dict:
        """Lấy thông tin topic"""
        return {
            "topic": topic,
            "subscribers": len(self.topic_subscriptions.get(topic, [])),
            "connection_ids": self.topic_subscriptions.get(topic, [])
        }

# Global WebSocket Bridge instance
mqtt_websocket_bridge = MQTTWebSocketBridge()
