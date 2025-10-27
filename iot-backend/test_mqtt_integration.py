#!/usr/bin/env python3
"""
Test script để kiểm tra tích hợp MQTT và HTTP API
"""
import requests
import json
import time
import threading
import paho.mqtt.client as mqtt
import websocket
import sys

# Configuration
API_BASE_URL = "http://localhost:8000"
MQTT_BROKER_HOST = "localhost"
MQTT_BROKER_PORT = 1883
WEBSOCKET_URL = "ws://localhost:8000/ws/mqtt"

class MQTTIntegrationTester:
    def __init__(self):
        self.api_base = API_BASE_URL
        self.mqtt_client = None
        self.websocket = None
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
        
    def test_http_api_health(self):
        """Test HTTP API health"""
        try:
            response = requests.get(f"{self.api_base}/health")
            if response.status_code == 200:
                data = response.json()
                self.log_test("HTTP API Health", True, f"Status: {data.get('status')}")
                return True
            else:
                self.log_test("HTTP API Health", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("HTTP API Health", False, f"Error: {e}")
            return False
            
    def test_mqtt_api_endpoints(self):
        """Test MQTT API endpoints"""
        try:
            # Test MQTT status
            response = requests.get(f"{self.api_base}/mqtt/status")
            if response.status_code == 200:
                self.log_test("MQTT Status API", True, "Endpoint accessible")
            else:
                self.log_test("MQTT Status API", False, f"Status code: {response.status_code}")
                
            # Test start MQTT broker
            response = requests.post(f"{self.api_base}/mqtt/start")
            if response.status_code == 200:
                self.log_test("Start MQTT Broker", True, "Broker started")
                time.sleep(2)  # Wait for broker to start
            else:
                self.log_test("Start MQTT Broker", False, f"Status code: {response.status_code}")
                
            # Test MQTT status again
            response = requests.get(f"{self.api_base}/mqtt/status")
            if response.status_code == 200:
                data = response.json()
                if data.get("running"):
                    self.log_test("MQTT Broker Running", True, "Broker is running")
                else:
                    self.log_test("MQTT Broker Running", False, "Broker not running")
            else:
                self.log_test("MQTT Status Check", False, f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_test("MQTT API Endpoints", False, f"Error: {e}")
            
    def test_mqtt_connection(self):
        """Test MQTT client connection"""
        try:
            self.mqtt_client = mqtt.Client()
            
            def on_connect(client, userdata, flags, rc):
                if rc == 0:
                    self.log_test("MQTT Connection", True, "Connected to broker")
                else:
                    self.log_test("MQTT Connection", False, f"Connection failed: {rc}")
                    
            def on_message(client, userdata, msg):
                self.log_test("MQTT Message Received", True, f"Topic: {msg.topic}, Message: {msg.payload.decode()}")
                
            self.mqtt_client.on_connect = on_connect
            self.mqtt_client.on_message = on_message
            
            self.mqtt_client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
            self.mqtt_client.loop_start()
            
            # Subscribe to test topic
            test_topic = "test/integration"
            self.mqtt_client.subscribe(test_topic)
            self.log_test("MQTT Subscribe", True, f"Subscribed to {test_topic}")
            
            # Publish test message
            test_message = "Hello from integration test!"
            self.mqtt_client.publish(test_topic, test_message)
            self.log_test("MQTT Publish", True, f"Published to {test_topic}")
            
            time.sleep(2)  # Wait for message
            
        except Exception as e:
            self.log_test("MQTT Connection", False, f"Error: {e}")
            
    def test_websocket_connection(self):
        """Test WebSocket connection"""
        try:
            def on_message(ws, message):
                data = json.loads(message)
                if data.get("type") == "connection":
                    self.log_test("WebSocket Connection", True, f"Connected: {data.get('connection_id')}")
                elif data.get("type") == "mqtt_message":
                    self.log_test("WebSocket MQTT Message", True, f"Received: {data.get('topic')} -> {data.get('message')}")
                    
            def on_error(ws, error):
                self.log_test("WebSocket Error", False, f"Error: {error}")
                
            def on_close(ws, close_status_code, close_msg):
                self.log_test("WebSocket Close", True, "Connection closed")
                
            def on_open(ws):
                self.log_test("WebSocket Open", True, "WebSocket opened")
                
                # Subscribe to test topic
                subscribe_msg = {
                    "action": "subscribe",
                    "topic": "test/websocket"
                }
                ws.send(json.dumps(subscribe_msg))
                
                # Publish test message via HTTP API
                time.sleep(1)
                self.test_websocket_publish()
                
            self.websocket = websocket.WebSocketApp(
                WEBSOCKET_URL,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )
            
            # Run WebSocket in separate thread
            ws_thread = threading.Thread(target=self.websocket.run_forever)
            ws_thread.daemon = True
            ws_thread.start()
            
            time.sleep(5)  # Wait for WebSocket operations
            
        except Exception as e:
            self.log_test("WebSocket Connection", False, f"Error: {e}")
            
    def test_websocket_publish(self):
        """Test publishing message via HTTP API"""
        try:
            # Publish message via HTTP API
            publish_data = {
                "topic": "test/websocket",
                "message": "Hello from HTTP API!"
            }
            
            response = requests.post(
                f"{self.api_base}/mqtt/publish",
                json=publish_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                self.log_test("HTTP Publish", True, "Message published via HTTP API")
            else:
                self.log_test("HTTP Publish", False, f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_test("HTTP Publish", False, f"Error: {e}")
            
    def test_sensor_data_flow(self):
        """Test complete sensor data flow"""
        try:
            # Simulate sensor data via HTTP API
            sensor_data = {
                "device_token": "test_device_123",
                "virtual_pin": 1,
                "value": "25.5"
            }
            
            response = requests.post(
                f"{self.api_base}/mqtt/sensor-data",
                params=sensor_data
            )
            
            if response.status_code == 200:
                self.log_test("Sensor Data Flow", True, "Sensor data sent successfully")
            else:
                self.log_test("Sensor Data Flow", False, f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_test("Sensor Data Flow", False, f"Error: {e}")
            
    def cleanup(self):
        """Cleanup resources"""
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            
        if self.websocket:
            self.websocket.close()
            
    def run_all_tests(self):
        """Run all integration tests"""
        print("🧪 Starting MQTT-HTTP Integration Tests...")
        print("=" * 60)
        
        # Test HTTP API
        print("\n📡 Testing HTTP API...")
        self.test_http_api_health()
        
        # Test MQTT API endpoints
        print("\n🔌 Testing MQTT API Endpoints...")
        self.test_mqtt_api_endpoints()
        
        # Test MQTT connection
        print("\n📡 Testing MQTT Connection...")
        self.test_mqtt_connection()
        
        # Test WebSocket
        print("\n🌐 Testing WebSocket Connection...")
        self.test_websocket_connection()
        
        # Test sensor data flow
        print("\n📊 Testing Sensor Data Flow...")
        self.test_sensor_data_flow()
        
        # Cleanup
        self.cleanup()
        
        # Print results
        print("\n" + "=" * 60)
        print("📋 Test Results Summary:")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
            
        print(f"\n🎯 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! MQTT-HTTP integration is working!")
        else:
            print("⚠️ Some tests failed. Check the errors above.")
            
        return passed == total

def main():
    """Main function"""
    print("🚀 MQTT-HTTP Integration Tester")
    print("=" * 60)
    print("Make sure the IoT Backend API is running on http://localhost:8000")
    print("Press Enter to continue or Ctrl+C to cancel...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\n👋 Test cancelled by user")
        return
        
    tester = MQTTIntegrationTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 Integration test completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Integration test failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
