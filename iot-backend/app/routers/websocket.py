# WebSocket endpoints
# app/routers/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import HTMLResponse
import json
import uuid
from app.websockets.mqtt_bridge import mqtt_websocket_bridge
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/ws", tags=["WebSocket"])

@router.websocket("/mqtt")
async def websocket_mqtt_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint để kết nối với MQTT
    
    Protocol:
    - Client gửi: {"action": "subscribe", "topic": "sensor/device1/1"}
    - Server gửi: {"type": "mqtt_message", "topic": "sensor/device1/1", "message": "25.5"}
    """
    connection_id = str(uuid.uuid4())
    
    try:
        await mqtt_websocket_bridge.connect(websocket, connection_id)
        
        # Gửi welcome message
        await websocket.send_text(json.dumps({
            "type": "connection",
            "message": "Connected to MQTT WebSocket Bridge",
            "connection_id": connection_id
        }))
        
        while True:
            # Nhận message từ client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            action = message.get("action")
            topic = message.get("topic")
            
            if action == "subscribe":
                if topic:
                    success = await mqtt_websocket_bridge.subscribe_topic(connection_id, topic)
                    await websocket.send_text(json.dumps({
                        "type": "subscription",
                        "topic": topic,
                        "success": success,
                        "message": f"Subscribed to {topic}" if success else f"Failed to subscribe to {topic}"
                    }))
                else:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Topic is required for subscribe action"
                    }))
                    
            elif action == "unsubscribe":
                if topic:
                    success = await mqtt_websocket_bridge.unsubscribe_topic(connection_id, topic)
                    await websocket.send_text(json.dumps({
                        "type": "unsubscription",
                        "topic": topic,
                        "success": success,
                        "message": f"Unsubscribed from {topic}" if success else f"Failed to unsubscribe from {topic}"
                    }))
                else:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Topic is required for unsubscribe action"
                    }))
                    
            elif action == "ping":
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "message": "pong"
                }))
                
            else:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Unknown action: {action}"
                }))
                
    except WebSocketDisconnect:
        mqtt_websocket_bridge.disconnect(connection_id)
        print(f"🔌 WebSocket disconnected: {connection_id}")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        mqtt_websocket_bridge.disconnect(connection_id)

@router.get("/mqtt/test")
async def websocket_test_page():
    """Test page cho WebSocket MQTT Bridge"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>MQTT WebSocket Test</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .container { max-width: 800px; margin: 0 auto; }
            .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
            input, button { margin: 5px; padding: 8px; }
            button { background: #007bff; color: white; border: none; border-radius: 3px; cursor: pointer; }
            button:hover { background: #0056b3; }
            #messages { height: 300px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; background: #f9f9f9; }
            .message { margin: 5px 0; padding: 5px; border-radius: 3px; }
            .mqtt-message { background: #e7f3ff; border-left: 3px solid #007bff; }
            .system-message { background: #fff3cd; border-left: 3px solid #ffc107; }
            .error-message { background: #f8d7da; border-left: 3px solid #dc3545; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔌 MQTT WebSocket Test</h1>
            
            <div class="section">
                <h3>Connection</h3>
                <button onclick="connect()">Connect</button>
                <button onclick="disconnect()">Disconnect</button>
                <span id="status">Disconnected</span>
            </div>
            
            <div class="section">
                <h3>Subscribe to Topic</h3>
                <input type="text" id="subscribeTopic" placeholder="sensor/device1/1" value="sensor/device1/1">
                <button onclick="subscribe()">Subscribe</button>
            </div>
            
            <div class="section">
                <h3>Unsubscribe from Topic</h3>
                <input type="text" id="unsubscribeTopic" placeholder="sensor/device1/1" value="sensor/device1/1">
                <button onclick="unsubscribe()">Unsubscribe</button>
            </div>
            
            <div class="section">
                <h3>Messages</h3>
                <div id="messages"></div>
                <button onclick="clearMessages()">Clear</button>
            </div>
        </div>

        <script>
            let ws = null;
            let connectionId = null;

            function connect() {
                if (ws) {
                    ws.close();
                }
                
                ws = new WebSocket('ws://localhost:8000/ws/mqtt');
                
                ws.onopen = function(event) {
                    document.getElementById('status').textContent = 'Connected';
                    addMessage('Connected to WebSocket', 'system-message');
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    console.log('Received:', data);
                    
                    if (data.type === 'connection') {
                        connectionId = data.connection_id;
                        addMessage(`Connection ID: ${connectionId}`, 'system-message');
                    } else if (data.type === 'mqtt_message') {
                        addMessage(`MQTT: ${data.topic} -> ${data.message}`, 'mqtt-message');
                    } else if (data.type === 'subscription') {
                        addMessage(`Subscribed to ${data.topic}: ${data.success}`, 'system-message');
                    } else if (data.type === 'unsubscription') {
                        addMessage(`Unsubscribed from ${data.topic}: ${data.success}`, 'system-message');
                    } else if (data.type === 'error') {
                        addMessage(`Error: ${data.message}`, 'error-message');
                    }
                };
                
                ws.onclose = function(event) {
                    document.getElementById('status').textContent = 'Disconnected';
                    addMessage('Disconnected from WebSocket', 'system-message');
                };
                
                ws.onerror = function(error) {
                    addMessage(`WebSocket error: ${error}`, 'error-message');
                };
            }

            function disconnect() {
                if (ws) {
                    ws.close();
                }
            }

            function subscribe() {
                const topic = document.getElementById('subscribeTopic').value;
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({
                        action: 'subscribe',
                        topic: topic
                    }));
                } else {
                    addMessage('Not connected to WebSocket', 'error-message');
                }
            }

            function unsubscribe() {
                const topic = document.getElementById('unsubscribeTopic').value;
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({
                        action: 'unsubscribe',
                        topic: topic
                    }));
                } else {
                    addMessage('Not connected to WebSocket', 'error-message');
                }
            }

            function addMessage(message, className) {
                const messagesDiv = document.getElementById('messages');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${className}`;
                messageDiv.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
                messagesDiv.appendChild(messageDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }

            function clearMessages() {
                document.getElementById('messages').innerHTML = '';
            }

            // Auto-connect on page load
            window.onload = function() {
                connect();
            };
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@router.get("/mqtt/connections")
def get_websocket_connections():
    """Lấy thông tin tất cả WebSocket connections"""
    try:
        connections = mqtt_websocket_bridge.get_all_connections()
        return {
            "connections": connections,
            "total": len(connections)
        }
    except Exception as e:
        return {"error": f"Failed to get connections: {str(e)}"}

@router.get("/mqtt/topics")
def get_websocket_topics():
    """Lấy thông tin tất cả topics và subscribers"""
    try:
        topics = []
        for topic in mqtt_websocket_bridge.topic_subscriptions:
            topics.append(mqtt_websocket_bridge.get_topic_info(topic))
        return {
            "topics": topics,
            "total": len(topics)
        }
    except Exception as e:
        return {"error": f"Failed to get topics: {str(e)}"}
