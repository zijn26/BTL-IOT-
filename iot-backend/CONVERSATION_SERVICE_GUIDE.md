# 📘 CONVERSATION SERVICE - Multi-User Guide

## 🎯 Tổng quan

**Conversation Service** đã được nâng cấp để hỗ trợ **multi-user** với lưu trữ lịch sử hội thoại riêng biệt theo `client_id`.

### ✨ Tính năng chính:
- ✅ Lưu trữ conversation history theo client_id
- ✅ Hỗ trợ nhiều người dùng cùng lúc
- ✅ Thread-safe (an toàn với concurrent requests)
- ✅ Auto cleanup sessions cũ (timeout 30 phút)
- ✅ Giới hạn history (20 messages mỗi client)
- ✅ API endpoints để quản lý conversations

---

## 🚀 Cách sử dụng

### **1. Chat với AI (với client_id)**

```bash
POST http://localhost:8000/ai/chat
Content-Type: application/json

{
  "client_id": "user_123",
  "message": "Bật đèn phòng khách",
  "metadata": {
    "user_name": "Nguyễn Văn A",
    "device_type": "mobile"
  }
}
```

**Response:**
```json
{
  "client_id": "user_123",
  "response": "Đã bật đèn phòng khách thành công!",
  "tool_calls": [
    {
      "name": "turn_on_device",
      "arguments": {"device_name": "Đèn phòng khách"},
      "result": "OK"
    }
  ],
  "message_count": 2
}
```

---

### **2. Lấy lịch sử hội thoại**

```bash
GET http://localhost:8000/ai/conversation/user_123
```

**Response:**
```json
{
  "client_id": "user_123",
  "history": [
    {"role": "user", "content": "Bật đèn phòng khách"},
    {"role": "assistant", "content": "Đã bật đèn phòng khách thành công!"}
  ],
  "message_count": 2,
  "metadata": {
    "user_name": "Nguyễn Văn A",
    "device_type": "mobile"
  }
}
```

---

### **3. Xóa lịch sử hội thoại**

```bash
DELETE http://localhost:8000/ai/conversation/user_123
```

**Response:**
```json
{
  "message": "Đã xóa conversation của client user_123",
  "success": true
}
```

---

### **4. Liệt kê tất cả conversations**

```bash
GET http://localhost:8000/ai/conversations
```

**Response:**
```json
{
  "total_active_clients": 3,
  "total_messages": 12,
  "clients": {
    "user_123": {
      "message_count": 4,
      "last_activity": "2025-01-20T10:30:00",
      "metadata": {"user_name": "Nguyễn Văn A"}
    },
    "user_456": {
      "message_count": 6,
      "last_activity": "2025-01-20T10:25:00",
      "metadata": {"user_name": "Trần Thị B"}
    }
  }
}
```

---

### **5. Lấy danh sách client IDs**

```bash
GET http://localhost:8000/ai/conversations/clients
```

**Response:**
```json
{
  "clients": ["user_123", "user_456", "esp32_001"],
  "count": 3
}
```

---

## 💻 Sử dụng trong Python Code

### **Import service:**
```python
from app.services.conversation_service import conversation_service
```

### **Chat với AI:**
```python
# Chat với user_123
result = await conversation_service.chat(
    client_id="user_123",
    user_message="Bật đèn phòng khách",
    metadata={"user_name": "Nguyễn Văn A"}
)

print(result["response"])
# → "Đã bật đèn phòng khách thành công!"
```

### **Lấy lịch sử:**
```python
history = conversation_service.get_conversation_history("user_123")
print(f"User có {len(history)} messages")
```

### **Xóa lịch sử:**
```python
conversation_service.clear_conversation("user_123")
```

### **Lấy thống kê:**
```python
stats = conversation_service.get_statistics()
print(f"Có {stats['total_active_clients']} clients đang hoạt động")
```

---

## 🎯 Use Cases

### **Use Case 1: Voice Assistant trên ESP32**

```python
# Trong audio_stream.py
from app.services.conversation_service import conversation_service

@router.websocket("/ws/{client_id}")
async def audio_stream(websocket: WebSocket, client_id: str):
    # ... Nhận audio và STT ...
    
    text = stt_result  # "Bật đèn phòng khách"
    
    # Chat với AI (tự động lưu history theo client_id)
    result = await conversation_service.process_voice_command(
        client_id=client_id,
        text=text,
        metadata={"device_type": "ESP32"}
    )
    
    response_text = result  # "Đã bật đèn"
    
    # TTS và gửi về ESP32
    # ...
```

**Lợi ích:**
- ✅ Mỗi ESP32 có context riêng
- ✅ AI nhớ lịch sử hội thoại trước đó
- ✅ Hiểu được context: "Bật nó lên" (AI biết "nó" là đèn phòng khách)

---

### **Use Case 2: Web/Mobile App**

```python
# Frontend gửi request với user_id
POST /ai/chat
{
  "client_id": "user_nguyenvana@gmail.com",
  "message": "Nhiệt độ phòng khách là bao nhiêu?"
}

# Backend tự động:
# 1. Lấy history của user này
# 2. Xử lý request với context
# 3. Lưu lại conversation
# 4. Return response
```

**Lợi ích:**
- ✅ Mỗi user có conversation riêng
- ✅ AI nhớ những gì user đã hỏi
- ✅ Context-aware responses

---

### **Use Case 3: Multi-Device cho cùng 1 user**

```python
# User dùng mobile
POST /ai/chat
{
  "client_id": "user_123",
  "message": "Bật đèn phòng khách"
}

# Sau đó user chuyển sang web, vẫn có context
GET /ai/conversation/user_123
# → Lấy được lịch sử: "Bật đèn phòng khách"

# User hỏi tiếp trên web
POST /ai/chat
{
  "client_id": "user_123",
  "message": "Tắt nó đi"
}
# → AI hiểu "nó" = "đèn phòng khách"
```

---

## ⚙️ Cấu hình

### **Trong `conversation_service.py`:**

```python
class ConversationService:
    def __init__(self):
        # Giới hạn số messages trong history
        self.max_history_length = 20
        
        # Timeout cho session không hoạt động (phút)
        self.session_timeout_minutes = 30
```

### **Thay đổi cấu hình:**

```python
# Tăng giới hạn history
conversation_service.max_history_length = 50

# Tăng timeout
conversation_service.session_timeout_minutes = 60
```

---

## 🔒 Thread Safety

Service đã được thiết kế **thread-safe** để handle nhiều requests đồng thời:

```python
# Lock để đảm bảo thread-safe
self.lock = threading.Lock()

# Tất cả operations đều được protect
with self.lock:
    self.conversations[client_id] = {...}
```

**Kết quả:**
- ✅ Nhiều users có thể chat đồng thời
- ✅ Không bị race conditions
- ✅ Data consistency được đảm bảo

---

## 🧹 Auto Cleanup

Service tự động xóa các session cũ không hoạt động:

```python
# Mỗi lần chat, tự động cleanup sessions > 30 phút
self._cleanup_old_sessions()
```

**Lợi ích:**
- ✅ Tiết kiệm memory
- ✅ Không bị memory leak
- ✅ Tự động dọn dẹp

---

## 📊 Monitoring & Statistics

### **Xem thống kê:**
```python
stats = conversation_service.get_statistics()

print(f"Active clients: {stats['total_active_clients']}")
print(f"Total messages: {stats['total_messages']}")

for client_id, info in stats['clients'].items():
    print(f"  {client_id}: {info['message_count']} messages")
```

### **API để monitor:**
```bash
GET /ai/conversations
```

---

## 🎨 Client ID Strategies

### **Strategy 1: User ID**
```python
client_id = "user_nguyenvana@gmail.com"
```
- ✅ Phù hợp: Web/Mobile app
- ✅ Context across devices

### **Strategy 2: Device ID**
```python
client_id = "esp32_living_room"
```
- ✅ Phù hợp: IoT devices
- ✅ Context per device

### **Strategy 3: Session ID**
```python
client_id = f"session_{uuid.uuid4()}"
```
- ✅ Phù hợp: Anonymous users
- ✅ Temporary conversations

### **Strategy 4: Hybrid**
```python
client_id = f"user_123_device_esp32"
```
- ✅ Phù hợp: User + Device tracking
- ✅ Most granular

---

## 🐛 Troubleshooting

### **Issue 1: History không được lưu**

**Kiểm tra:**
```python
# Xem có client_id trong conversations không
clients = conversation_service.get_all_active_clients()
print(clients)
```

**Nguyên nhân:**
- Timeout quá ngắn
- Session bị cleanup

**Giải pháp:**
```python
conversation_service.session_timeout_minutes = 60
```

---

### **Issue 2: History quá dài**

**Kiểm tra:**
```python
history = conversation_service.get_conversation_history(client_id)
print(f"History length: {len(history)}")
```

**Giải pháp:**
```python
# Giảm max_history_length
conversation_service.max_history_length = 10

# Hoặc clear conversation
conversation_service.clear_conversation(client_id)
```

---

### **Issue 3: Multiple clients conflict**

**Đảm bảo client_id unique:**
```python
# BAD: Dùng cùng 1 client_id cho nhiều users
client_id = "default"

# GOOD: Unique client_id
client_id = f"user_{user_email}"
```

---

## 📝 Migration từ version cũ

### **Version cũ (không có client_id):**
```python
result = await conversation_service.chat(
    user_message="Bật đèn",
    conversation_history=[]
)
```

### **Version mới (có client_id):**
```python
result = await conversation_service.chat(
    client_id="user_123",
    user_message="Bật đèn"
    # conversation_history tự động được lấy
)
```

**Changes:**
- ✅ Bắt buộc phải có `client_id`
- ✅ Không cần truyền `conversation_history` (tự động)
- ✅ Thêm `metadata` (optional)

---

## 🎉 Summary

| Feature | Old Version | New Version |
|---------|-------------|-------------|
| Multi-user | ❌ | ✅ |
| Auto save history | ❌ | ✅ |
| Thread-safe | ❌ | ✅ |
| Auto cleanup | ❌ | ✅ |
| API endpoints | 2 | 7 |
| Metadata support | ❌ | ✅ |

**Đã sẵn sàng để sử dụng! 🚀**

