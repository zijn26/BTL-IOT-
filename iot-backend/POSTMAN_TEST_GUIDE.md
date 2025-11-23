# 🧪 HƯỚNG DẪN TEST API TRÊN POSTMAN

## 🚀 Quick Start

### **Bước 1: Start Server**
```bash
cd d:\IOTBTL\iot-backend
uvicorn app.main:app --reload
```

Server chạy tại: `http://localhost:8000`

---

## 📋 DANH SÁCH ENDPOINTS

### **1. Lấy danh sách Tools (với examples)**

```
GET http://localhost:8000/ai/tools
```

**Response:**
```json
{
  "total": 8,
  "tools": [
    {
      "name": "turn_on_device",
      "description": "Bật thiết bị IoT theo tên thiết bị",
      "parameters": {...},
      "required": ["device_name"],
      "example_request": {
        "tool_name": "turn_on_device",
        "arguments": {
          "device_name": "Đèn phòng khách"
        }
      }
    },
    ...
  ],
  "usage": "Copy 'example_request' và paste vào Body của POST /ai/execute-tool",
  "endpoint": "POST /ai/execute-tool"
}
```

💡 **Tip:** Copy `example_request` từ response này để test!

---

### **2. Test Tool trực tiếp**

```
POST http://localhost:8000/ai/execute-tool
Content-Type: application/json
```

**Body:**
```json
{
  "tool_name": "turn_on_device",
  "arguments": {
    "device_name": "Đèn phòng khách"
  }
}
```

**Response:**
```json
{
  "tool": "turn_on_device",
  "arguments": {
    "device_name": "Đèn phòng khách"
  },
  "result": "Đã bật thiết bị 'Đèn phòng khách' thành công",
  "success": true
}
```

---

### **3. Chat với AI**

```
POST http://localhost:8000/ai/chat
Content-Type: application/json
```

**Body:**
```json
{
  "client_id": "test_user",
  "message": "Bật đèn phòng khách"
}
```

**Response:**
```json
{
  "client_id": "test_user",
  "response": "Đã bật đèn phòng khách thành công!",
  "tool_calls": [
    {
      "name": "turn_on_device",
      "arguments": {"device_name": "Đèn phòng khách"},
      "result": "Đã bật thiết bị 'Đèn phòng khách' thành công"
    }
  ],
  "message_count": 2
}
```

---

## 🎯 EXAMPLES CHO TỪNG TOOL

### **Tool 1: Bật thiết bị**
```json
{
  "tool_name": "turn_on_device",
  "arguments": {
    "device_name": "Đèn phòng khách"
  }
}
```

### **Tool 2: Tắt thiết bị**
```json
{
  "tool_name": "turn_off_device",
  "arguments": {
    "device_name": "Quạt phòng ngủ"
  }
}
```

### **Tool 3: Điều chỉnh độ sáng**
```json
{
  "tool_name": "set_brightness",
  "arguments": {
    "device_name": "Đèn phòng khách",
    "brightness": 75
  }
}
```

### **Tool 4: Đọc nhiệt độ**
```json
{
  "tool_name": "read_temperature",
  "arguments": {
    "sensor_name": "Cảm biến phòng khách"
  }
}
```

### **Tool 5: Đọc độ ẩm**
```json
{
  "tool_name": "read_humidity",
  "arguments": {
    "sensor_name": "Cảm biến phòng khách"
  }
}
```

### **Tool 6: Liệt kê tất cả thiết bị**
```json
{
  "tool_name": "list_all_devices",
  "arguments": {}
}
```

### **Tool 7: Kiểm tra trạng thái thiết bị**
```json
{
  "tool_name": "check_device_status",
  "arguments": {
    "device_name": "Đèn phòng khách"
  }
}
```

### **Tool 8: Hẹn giờ bật thiết bị**
```json
{
  "tool_name": "schedule_turn_on",
  "arguments": {
    "device_name": "Đèn phòng khách",
    "delay_seconds": 10
  }
}
```

---

## 📝 POSTMAN COLLECTION

### **Collection: IoT Backend API**

#### **Folder 1: Tools**

**Request 1.1: Get All Tools**
- Method: `GET`
- URL: `{{base_url}}/ai/tools`
- Headers: (none)
- Body: (none)

**Request 1.2: Execute Tool - Turn On Device**
- Method: `POST`
- URL: `{{base_url}}/ai/execute-tool`
- Headers: `Content-Type: application/json`
- Body (raw JSON):
```json
{
  "tool_name": "turn_on_device",
  "arguments": {
    "device_name": "Đèn phòng khách"
  }
}
```

**Request 1.3: Execute Tool - Turn Off Device**
- Method: `POST`
- URL: `{{base_url}}/ai/execute-tool`
- Body:
```json
{
  "tool_name": "turn_off_device",
  "arguments": {
    "device_name": "Đèn phòng khách"
  }
}
```

**Request 1.4: Execute Tool - List All Devices**
- Method: `POST`
- URL: `{{base_url}}/ai/execute-tool`
- Body:
```json
{
  "tool_name": "list_all_devices",
  "arguments": {}
}
```

#### **Folder 2: AI Chat**

**Request 2.1: Chat with AI**
- Method: `POST`
- URL: `{{base_url}}/ai/chat`
- Body:
```json
{
  "client_id": "postman_test",
  "message": "Bật đèn phòng khách"
}
```

**Request 2.2: Get Conversation History**
- Method: `GET`
- URL: `{{base_url}}/ai/conversation/postman_test`

**Request 2.3: Clear Conversation**
- Method: `DELETE`
- URL: `{{base_url}}/ai/conversation/postman_test`

**Request 2.4: List All Conversations**
- Method: `GET`
- URL: `{{base_url}}/ai/conversations`

---

## ⚙️ SETUP POSTMAN

### **Bước 1: Tạo Environment**

Environment Name: `IoT Backend Local`

Variables:
```
base_url = http://localhost:8000
```

### **Bước 2: Import Collection**

1. Tạo Collection mới: "IoT Backend API"
2. Add các requests theo structure trên
3. Sử dụng `{{base_url}}` thay vì hardcode URL

---

## 🧪 TEST FLOW

### **Scenario 1: Test một tool đơn giản**

1. **Start server**
   ```bash
   uvicorn app.main:app --reload
   ```

2. **Lấy danh sách tools**
   ```
   GET /ai/tools
   ```

3. **Copy example_request từ tool bạn muốn test**

4. **Paste vào body của POST /ai/execute-tool**

5. **Click Send**

6. **Xem result trong response**

---

### **Scenario 2: Test chat với AI**

1. **Chat lần 1**
   ```json
   POST /ai/chat
   {
     "client_id": "test_user_123",
     "message": "Bật đèn phòng khách"
   }
   ```

2. **Chat lần 2 (có context)**
   ```json
   POST /ai/chat
   {
     "client_id": "test_user_123",
     "message": "Tắt nó đi"
   }
   ```
   → AI hiểu "nó" = "đèn phòng khách"

3. **Xem lịch sử**
   ```
   GET /ai/conversation/test_user_123
   ```

4. **Xóa lịch sử**
   ```
   DELETE /ai/conversation/test_user_123
   ```

---

## 🎬 VIDEO DEMO

### **Test Tool trên Postman:**

1. Mở Postman
2. Tạo request mới: `POST http://localhost:8000/ai/execute-tool`
3. Chọn Body → raw → JSON
4. Paste:
   ```json
   {
     "tool_name": "list_all_devices",
     "arguments": {}
   }
   ```
5. Click Send
6. Xem response:
   ```json
   {
     "tool": "list_all_devices",
     "arguments": {},
     "result": "Danh sách thiết bị:\n1. Đèn phòng khách (light) - online\n...",
     "success": true
   }
   ```

---

## 🐛 TROUBLESHOOTING

### **Lỗi: No tools found**

**Nguyên nhân:** Tools chưa được import

**Giải pháp:**
1. Check `app/tools/__init__.py` có uncomment dòng import không
2. Restart server
3. Check console có thấy "✅ Đã đăng ký tool..." không

---

### **Lỗi: Tool not found**

**Nguyên nhân:** Tool name sai

**Giải pháp:**
1. GET `/ai/tools` để xem danh sách tool names chính xác
2. Copy exact tool name từ response
3. Test lại

---

### **Lỗi: 422 Validation Error**

**Nguyên nhân:** Body format sai

**Giải pháp:**
1. Check Content-Type header: `application/json`
2. Check body là valid JSON
3. Check có đủ required fields không
4. Copy example từ `/ai/tools` để chắc chắn format đúng

---

## 📊 EXPECTED RESPONSES

### **✅ Success:**
```json
{
  "tool": "turn_on_device",
  "arguments": {...},
  "result": "Đã bật thiết bị thành công",
  "success": true
}
```

### **❌ Tool Not Found:**
```json
{
  "tool": "invalid_tool",
  "arguments": {},
  "result": "Error: Tool invalid_tool not found",
  "success": true
}
```

### **❌ Device Not Found:**
```json
{
  "tool": "turn_on_device",
  "arguments": {"device_name": "Unknown Device"},
  "result": "Không tìm thấy thiết bị 'Unknown Device'",
  "success": true
}
```

---

## 🎉 TIPS

1. **Lưu requests vào Collection** để reuse
2. **Dùng Environment variables** cho base_url
3. **Test từ đơn giản đến phức tạp**: tools → chat → conversations
4. **Copy examples từ `/ai/tools`** thay vì tự viết
5. **Check console logs** khi test để debug

---

**Happy Testing! 🚀**

