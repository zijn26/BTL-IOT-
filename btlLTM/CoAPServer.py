
"""
CoAP Server đơn giản bằng Python thuần
Chỉ sử dụng socket UDP và threading cơ bản
"""
import json
import time
import socket
import threading
from CoAPMessageXuLI import CoAPContentFormat, CoAPMessage, CoAPCode, CoAPType, create_response
# {
#     "id": 1,
#     "data": 3.4,
#     "time": 1727164800
# }
class SimpleCoAPServer:
    """CoAP Server đơn giản"""

    def __init__(self, host: str = "127.0.0.1", port: int = 5683):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False # Dictionary: path -> in-memory store

        # Đăng ký default resources
        self.resources = {}
        # self.resources["/test/demo"] = [{} , { "id" : 1 , sds} , {} , {} ]  # Mảng lưu trữ các item JSON
    # def add_resource(self, path: str, resource ):
    #     """Thêm resource vào server"""
    #     self.resources[path] = resource
    #     print(f"📍 Registered resource: {path} -> {resource.name}")

    # def find_resource(self, path: str) -> SimpleCoAPResource:
    #     """Tìm resource theo path"""
    #     # Exact match trước
    #     if path in self.resources:
    #         return self.resources[path]

    #     # Fallback to root nếu không tìm thấy
    #     return self.resources.get("/", None)
    def handle_get(self, request: CoAPMessage, store) -> CoAPMessage:
        """Xử lý GET request - trả về phần tử mới nhất hoặc rỗng"""
        data = request.payload.decode('utf-8')
        obj = json.loads(data)
        if "id" in obj:
            for item in store:
                if item["id"] == obj["id"]:
                    payload = json.dumps(item).encode()
                    break
            else:
                payload = json.dumps({"message": "not found"}).encode()
        else:
            payload = json.dumps(store).encode()
        return create_response(request, CoAPCode.CONTENT, payload)

    def handle_post(self, request: CoAPMessage, store) -> CoAPMessage:
        """Xử lý POST request - lưu JSON {id,data,time} vào danh sách items"""
        try:
            data = request.payload.decode('utf-8')
            obj = json.loads(data)
            obj["recv_time"] = time.time()
            store.append(obj)
            return create_response(request, CoAPCode.CREATED, json.dumps({"message": "stored"}).encode())
        except Exception as e:
            err = {"error": f"invalid payload: {e}"}
            return create_response(request, CoAPCode.BAD_REQUEST, json.dumps(err).encode())

    def handle_put(self, request: CoAPMessage, store) -> CoAPMessage:
        """Xử lý PUT request - cập nhật item theo id nếu tồn tại"""
        try:
            data = request.payload.decode('utf-8')
            obj = json.loads(data)
            obj["recv_time"] = time.time()
           # duyet theo mang i de lay store[i] = obj
            for i in range(len(store)):
                if store[i].get("id") == obj.get("id"):
                    store[i] = obj
                    break
            return create_response(request, CoAPCode.CHANGED, json.dumps({"message": "updated"}).encode())
        except Exception as e:
            err = {"error": f"invalid payload: {e}"}
            return create_response(request, CoAPCode.BAD_REQUEST, json.dumps(err).encode())

    def handle_delete(self, request: CoAPMessage, store) -> CoAPMessage:
        """Xử lý DELETE request - xóa item theo id"""
        try:
            data = request.payload.decode('utf-8')
            obj = json.loads(data)
            for item in store:
                if item.get("id") == obj.get("id"):
                    store.remove(item)
                    break
            return create_response(request, CoAPCode.DELETED, json.dumps({"message": "deleted"}).encode())
        except Exception as e:
            err = {"error": f"invalid payload: {e}"}
            return create_response(request, CoAPCode.BAD_REQUEST, json.dumps(err).encode())
    def handle_request(self, data: bytes, client_address: tuple, dataBase):
        """Xử lý CoAP request"""
        try:
            # Parse request
            request = CoAPMessage.from_bytes(data)
            print(f"📥 Request from {client_address}: {request}")

            # Tìm resource
            path = request.get_uri_path()
            store = dataBase.setdefault(path, [])
            # Dispatch theo method
            if request.code == CoAPCode.GET:
                response = self.handle_get(request, store)
            elif request.code == CoAPCode.POST:
                response = self.handle_post(request, store)
            elif request.code == CoAPCode.PUT:
                response = self.handle_put(request, store)
            elif request.code == CoAPCode.DELETE:
                response = self.handle_delete(request, store)
            else:
                response = create_response(request, CoAPCode.METHOD_NOT_ALLOWED, b"Method not supported")

            # Gửi response
            response_data = response.to_bytes()
            self.socket.sendto(response_data, client_address)
            print(f"📤 Response to {client_address}: {response}")

        except Exception as e:
            print(f"❌ Error handling request from {client_address}: {e}")
            # Gửi error response nếu có thể
            try:
                error_response = CoAPMessage()
                error_response.msg_type = CoAPType.RST
                error_response.message_id = 0
                error_response.code = CoAPCode.INTERNAL_SERVER_ERROR
                error_response.set_content_format(CoAPContentFormat.JSON)
                error_response.payload = json.dumps({"error": str(e)}).encode()
                self.socket.sendto(error_response.to_bytes(), client_address)
            except:
                pass

    def start(self):
        """Khởi động CoAP server"""
        print(f"🚀 Starting CoAP Server on {self.host}:{self.port}")

        # Tạo UDP socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
        #socket.SOCK_DGRAM  là socket type cua UDP
        #socket.SO_REUSEADDR cho phep su dung lai port sau khi server dung
        # boi vi khi server dung, port van con duoc su dung do tcp van o che do time wait
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.socket.bind((self.host, self.port))
            print(f"✅ CoAP Server listening on {self.host}:{self.port}")
            print("📚 Available resources:")
            for path in self.resources.keys():
                print(f"   {path}")
          

            self.running = True

            # Main server loop
            while self.running:
                try:
                    # Nhận request (blocking)
                    data, client_address = self.socket.recvfrom(1024)

                    # Xử lý request trong thread riêng để không block
                    thread = threading.Thread(
                        target=self.handle_request, 
                        args=(data, client_address , self.resources),
                        daemon=True
                    )
                    thread.start()

                except socket.error as e:
                    if self.running:  # Chỉ log lỗi nếu server vẫn đang chạy
                        print(f"❌ Socket error: {e}")

        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user")
        except Exception as e:
            print(f"❌ Server error: {e}")
        finally:
            self.stop()

    def stop(self):
        """Dừng server"""
        self.running = False
        if self.socket:
            self.socket.close()
            print("🔌 Server socket closed")

if __name__ == "__main__":
    # Chạy server
    server = SimpleCoAPServer()

    try:
        server.start()
    except KeyboardInterrupt:
        print("\nBye! 👋")
