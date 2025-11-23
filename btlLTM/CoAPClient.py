
"""
CoAP Client đơn giản bằng Python thuần
Hỗ trợ các method cơ bản: GET, POST, PUT, DELETE
"""
import socket
import time
from CoAPMessageXuLI import CoAPMessage, CoAPCode, CoAPType, create_request

class SimpleCoAPClient:
    """CoAP Client đơn giản"""

    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout
        self.socket = None

    def _send_request(self, host: str, port: int, request: CoAPMessage) -> CoAPMessage:
        """Gửi request và nhận response"""
        # Tạo UDP socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(self.timeout)

        try:
            # Gửi request
            request_data = request.to_bytes()
            self.socket.sendto(request_data, (host, port))
            print(f"📤 Sent: {request}")

            # Nhận response
            response_data, server_address = self.socket.recvfrom(1024)
            response = CoAPMessage.from_bytes(response_data)
            print(f"📥 Received: {response}")

            return response

        except socket.timeout:
            print(f"⏰ Timeout after {self.timeout} seconds")
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
        finally:
            if self.socket:
                self.socket.close()

    def get(self, host: str, port: int, path: str , payload: str = "") -> CoAPMessage:
        """Gửi GET request"""
        request = create_request(CoAPCode.GET, path, payload.encode('utf-8'))
        return self._send_request(host, port, request)

    def post(self, host: str, port: int, path: str, payload: str = "") -> CoAPMessage:
        """Gửi POST request"""
        request = create_request(CoAPCode.POST, path, payload.encode('utf-8'))
        return self._send_request(host, port, request)

    def put(self, host: str, port: int, path: str, payload: str = "") -> CoAPMessage:
        """Gửi PUT request"""
        request = create_request(CoAPCode.PUT, path, payload.encode('utf-8'))
        return self._send_request(host, port, request)

    def delete(self, host: str, port: int, path: str , payload: str = "") -> CoAPMessage:
        """Gửi DELETE request"""
        request = create_request(CoAPCode.DELETE, path, payload.encode('utf-8'))
        return self._send_request(host, port, request)

def print_response(response: CoAPMessage):
    """In response một cách đẹp mắt"""
    if not response:
        print("❌ No response received")
        return

    print(f"\n📋 Response Details:")
    print(f"   Code: {response.code} ({response.code.name})")
    print(f"   Type: {response.msg_type.name}")
    print(f"   Message ID: {response.message_id}")
    print(f"   Payload Length: {len(response.payload)} bytes")

    if response.payload:
        try:
            payload_str = response.payload.decode('utf-8')
            print(f"   Payload: {payload_str}")
        except UnicodeDecodeError:
            print(f"   Payload (hex): {response.payload.hex()}")
    print()

def interactive_client():
    """CoAP Client tương tác"""
    print("🌐 Simple CoAP Client")
    print("=" * 50)

    client = SimpleCoAPClient()

    # Default server settings
    default_host = "127.0.0.1"
    default_port = 5683

    print(f"Default server: {default_host}:{default_port}")
    print("\nAvailable commands:")
    print("  get <path>           - GET request")
    print("  post <path> <data>   - POST request") 
    print("  put <path> <data>    - PUT request")
    print("  delete <path>        - DELETE request")
    print("  server <host> <port> - Change server")
    print("  test                 - Run test suite")
    print("  quit                 - Exit")
    print()

    host, port = default_host, default_port

    while True:
        try:
            command = input(f"coap://{host}:{port}> ").strip()

            if not command:
                continue

            parts = command.split()
            cmd = parts[0].lower()

            if cmd == "quit" or cmd == "exit":
                print("Bye! 👋")
                break

            elif cmd == "server":
                if len(parts) >= 3:
                    host = parts[1]
                    port = int(parts[2])
                    print(f"✅ Server changed to {host}:{port}")
                else:
                    print("❌ Usage: server <host> <port>")

            elif cmd == "get":
                if len(parts) >= 2:
                    path = parts[1]
                    response = client.get(host, port, path)
                    print_response(response)
                else:
                    print("❌ Usage: get <path>")

            elif cmd == "post":
                if len(parts) >= 2:
                    path = parts[1]
                    data = " ".join(parts[2:]) if len(parts) > 2 else ""
                    response = client.post(host, port, path, data)
                    print_response(response)
                else:
                    print("❌ Usage: post <path> [data]")

            elif cmd == "put":
                if len(parts) >= 2:
                    path = parts[1]
                    data = " ".join(parts[2:]) if len(parts) > 2 else ""
                    response = client.put(host, port, path, data)
                    print_response(response)
                else:
                    print("❌ Usage: put <path> [data]")

            elif cmd == "delete":
                if len(parts) >= 2:
                    path = parts[1]
                    response = client.delete(host, port, path)
                    print_response(response)
                else:
                    print("❌ Usage: delete <path>")

            elif cmd == "test":
                print("🧪 Running test suite...")
                run_test_suite(client, host, port)

            else:
                print(f"❌ Unknown command: {cmd}")

        except KeyboardInterrupt:
            print("\nBye! 👋")
            break
        except ValueError as e:
            print(f"❌ Invalid input: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")

def run_test_suite(client: SimpleCoAPClient, host: str, port: int):
    """Chạy test suite cơ bản"""
    tests = [
        ("GET /", lambda: client.get(host, port, "/")),
        ("GET /temperature", lambda: client.get(host, port, "/temperature")),
        ("GET /led", lambda: client.get(host, port, "/led")),
        ("POST /led ON", lambda: client.post(host, port, "/led", "ON")),
        ("GET /led (after ON)", lambda: client.get(host, port, "/led")),
        ("PUT /led 50", lambda: client.put(host, port, "/led", "50")),
        ("GET /led (after brightness)", lambda: client.get(host, port, "/led")),
        ("POST /led OFF", lambda: client.post(host, port, "/led", "OFF")),
        ("PUT /temperature 30.5", lambda: client.put(host, port, "/temperature", "30.5")),
        ("GET /temperature (after set)", lambda: client.get(host, port, "/temperature")),
    ]

    print(f"\n🧪 Testing CoAP server at {host}:{port}")
    print("-" * 60)

    success_count = 0
    for test_name, test_func in tests:
        print(f"\n🔍 Test: {test_name}")
        try:
            response = test_func()
            if response and response.code < 128:  # Success codes < 128
                print(f"✅ PASS")
                success_count += 1
            else:
                print(f"❌ FAIL - {response.code if response else 'No response'}")
        except Exception as e:
            print(f"❌ ERROR - {e}")

        time.sleep(0.5)  # Delay giữa các test

    print(f"\n📊 Test Results: {success_count}/{len(tests)} passed")
    print("-" * 60)

def demo_usage():
    """Demo usage examples"""
    print("🚀 CoAP Client Demo")
    print("=" * 50)

    client = SimpleCoAPClient()
    host, port = "127.0.0.1", 5683

    print("\n1. Testing temperature sensor:")
    response = client.get(host, port, "test/demo")
    print_response(response)

    print("2. Setting temperature:")
    response = client.put(host, port, "test/demo", "25.5")
    print_response(response)

    print("3. Testing LED control:")
    response = client.post(host, port, "test/demo", "ON")
    print_response(response)

    print("4. Setting LED brightness:")
    response = client.put(host, port, "test/demo", "75")
    print_response(response)

    print("5. Getting LED status:")
    response = client.get(host, port, "test/demo")
    print_response(response)

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo_usage()
    else:
        interactive_client()
